from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model

from billing.models import Invoice, InvoiceStatus, BillingFailure
from billing.generation import generate_invoice_for_subscription, InvoiceNotAllowed
from billing.services.allocation import (
    allocate_payment_to_invoice,
    reverse_payment_allocation,
    PaymentAllocationError,
)
from billing.services.recurring import (
    compute_next_period,
    process_subscription_billing,
    run_billing_sweep,
)

User = get_user_model()


class MockPlan:
    def __init__(self, name, billing_interval):
        self.name = name
        self.billing_interval = billing_interval


class MockSubscriptionLine:
    def __init__(self, description, quantity, unit_price, tax_rate=Decimal("0.00")):
        self.description = description
        self.quantity = Decimal(str(quantity))
        self.unit_price = Decimal(str(unit_price))
        self.discount_amount = Decimal("0.00")
        self.tax_rate = Decimal(str(tax_rate))


class MockSubscription:
    def __init__(self, id, user, status="active", expiry_date=None, lines=None, billing_interval="month", plan=None):
        self.id = id
        self.pk = id
        self.customer = user
        self.subscription_number = f"SUB-{id}"
        self.status = status
        self.currency = "INR"
        self.payment_terms_days = 15
        self.start_date = date(2026, 1, 1)
        self.billing_anchor_date = date(2026, 1, 1)
        self.next_billing_date = date(2026, 1, 1)
        self.expiry_date = expiry_date
        self.billing_interval = billing_interval
        self.plan = plan
        self.lines = lines or [
            MockSubscriptionLine("Enterprise SaaS", 1, Decimal("2000.00"), tax_rate=Decimal("18.00"))
        ]
        self.discount = None
        self.last_billed_period_end = None

    def save(self, update_fields=None):
        pass


@pytest.mark.django_db
def test_subscription_recurring_billing_flow():
    call_command("migrate", run_syncdb=True, verbosity=0)
    user = User.objects.create_user(username="client_sub", email="client@corp.com")

    sub = MockSubscription(id=101, user=user)
    p_start = date(2026, 1, 1)
    p_end = date(2026, 1, 31)

    # 1. Generate invoice for subscription period
    inv, created = generate_invoice_for_subscription(sub, p_start, p_end)
    assert created is True
    assert inv.subscription_id == "101"
    assert inv.subscription_number == "SUB-101"
    assert inv.period_start == p_start
    assert inv.period_end == p_end
    # 2000 + 18% tax (360) = 2360
    assert inv.subtotal == Decimal("2000.00")
    assert inv.tax_total == Decimal("360.00")
    assert inv.total == Decimal("2360.00")
    assert inv.amount_paid == Decimal("0.00")
    assert inv.outstanding_balance == Decimal("2360.00")
    assert inv.status == InvoiceStatus.DRAFT

    # 2. BILL-01: Idempotency / No duplicate invoice for same period
    inv_dup, created_dup = generate_invoice_for_subscription(sub, p_start, p_end)
    assert created_dup is False
    assert inv_dup.pk == inv.pk

    # 3. Checkpoint advancement (BILL-02)
    assert sub.last_billed_period_end == p_end
    assert sub.next_billing_date == date(2026, 2, 1)


@pytest.mark.django_db
def test_billing_intervals_suggested_by_plan():
    user = User.objects.create_user(username="interval_user", email="intervals@example.com")

    # Weekly plan
    sub_weekly = MockSubscription(id=601, user=user, plan=MockPlan("Weekly Pro", "weekly"))
    p_start, p_end = compute_next_period(sub_weekly)
    assert p_start == date(2026, 1, 1)
    assert p_end == date(2026, 1, 7)  # 7 days

    # Quarterly plan (every 3 months)
    sub_quarterly = MockSubscription(id=602, user=user, plan=MockPlan("Quarterly Pro", "quarterly"))
    p_start, p_end = compute_next_period(sub_quarterly)
    assert p_start == date(2026, 1, 1)
    assert p_end == date(2026, 3, 31)

    # Yearly plan
    sub_yearly = MockSubscription(id=603, user=user, plan=MockPlan("Annual Pro", "yearly"))
    p_start, p_end = compute_next_period(sub_yearly)
    assert p_start == date(2026, 1, 1)
    assert p_end == date(2026, 12, 31)


@pytest.mark.django_db
def test_paused_and_expired_subscriptions():
    user = User.objects.create_user(username="client_pause", email="pause@corp.com")

    # Paused subscription cannot generate invoice
    sub_paused = MockSubscription(id=202, user=user, status="paused")
    with pytest.raises(InvoiceNotAllowed, match="paused"):
        generate_invoice_for_subscription(sub_paused, date(2026, 2, 1), date(2026, 2, 28))

    # BILL-07: Expired subscription cannot bill past expiry
    sub_expired = MockSubscription(id=303, user=user, expiry_date=date(2026, 1, 31))
    with pytest.raises(InvoiceNotAllowed, match="exceeds expiry"):
        generate_invoice_for_subscription(sub_expired, date(2026, 2, 1), date(2026, 2, 28))


@pytest.mark.django_db
def test_payment_allocation_and_reversal():
    user = User.objects.create_user(username="pay_user", email="pay@example.com")
    sub = MockSubscription(id=404, user=user)
    inv, _ = generate_invoice_for_subscription(sub, date(2026, 3, 1), date(2026, 3, 31))

    total = inv.total  # 2360.00

    # 1. Partial payment (PRD §7.12 example: 1000 paid)
    inv = allocate_payment_to_invoice(inv.pk, Decimal("1000.00"))
    assert inv.amount_paid == Decimal("1000.00")
    assert inv.outstanding_balance == total - Decimal("1000.00")
    assert inv.is_partially_paid is True
    assert inv.status == InvoiceStatus.CONFIRMED

    # 2. PAY-03: Overpayment protection: payment exceeding outstanding balance is rejected
    excess = inv.outstanding_balance + Decimal("1.00")
    with pytest.raises(PaymentAllocationError, match="Overpayment rejected"):
        allocate_payment_to_invoice(inv.pk, excess)

    # 3. Second payment paying remaining balance marks status PAID
    rem = inv.outstanding_balance
    inv = allocate_payment_to_invoice(inv.pk, rem)
    assert inv.amount_paid == total
    assert inv.outstanding_balance == Decimal("0.00")
    assert inv.status == InvoiceStatus.PAID
    assert inv.is_partially_paid is False

    # 4. PAY-04: Reversal of payment reopens outstanding balance
    inv = reverse_payment_allocation(inv.pk, Decimal("500.00"))
    assert inv.amount_paid == total - Decimal("500.00")
    assert inv.outstanding_balance == Decimal("500.00")
    assert inv.status == InvoiceStatus.CONFIRMED


@pytest.mark.django_db
def test_invoice_cancellation_rules():
    user = User.objects.create_user(username="cancel_user", email="cancel@example.com")
    sub = MockSubscription(id=505, user=user)
    inv, _ = generate_invoice_for_subscription(sub, date(2026, 4, 1), date(2026, 4, 30))

    # Can cancel when amount_paid == 0
    assert inv.can_cancel is True

    # Allocate payment -> cannot cancel
    allocate_payment_to_invoice(inv.pk, Decimal("100.00"))
    inv.refresh_from_db()
    assert inv.can_cancel is False
