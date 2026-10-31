from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.customers.models import Customer, CustomerType, CustomerStatus
from apps.billing.models import Invoice, InvoiceStatus, BillingFailure
from apps.billing.generation import generate_invoice_for_subscription, InvoiceNotAllowed
from apps.billing.services.allocation import (
    allocate_payment_to_invoice,
    reverse_payment_allocation,
    PaymentAllocationError,
)
from apps.billing.services.recurring import (
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


class BillingModuleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="client@corp.com",
            first_name="Jane",
            last_name="Doe",
        )
        self.customer = Customer.objects.create(
            customer_code="CUST-CORP-01",
            display_name="Corp International",
            contact_person="Jane Doe",
            email="client@corp.com",
            billing_street="10 Tech Blvd",
            billing_city="Bengaluru",
            billing_state="Karnataka",
            billing_postal_code="560001",
            billing_country="India",
            customer_type=CustomerType.BUSINESS,
            status=CustomerStatus.ACTIVE,
            portal_user=self.user,
        )

    def test_subscription_recurring_billing_flow(self):
        """BILL-01 & BILL-02: Recurring draft invoice generation and checkpoint advancement."""
        sub = MockSubscription(id=101, user=self.customer)
        p_start = date(2026, 1, 1)
        p_end = date(2026, 1, 31)

        # 1. Generate invoice for subscription period
        inv, created = generate_invoice_for_subscription(sub, p_start, p_end)
        self.assertTrue(created)
        self.assertEqual(inv.subscription_id, "101")
        self.assertEqual(inv.subscription_number, "SUB-101")
        self.assertEqual(inv.period_start, p_start)
        self.assertEqual(inv.period_end, p_end)
        # 2000 + 18% tax (360) = 2360
        self.assertEqual(inv.subtotal, Decimal("2000.00"))
        self.assertEqual(inv.tax_total, Decimal("360.00"))
        self.assertEqual(inv.total, Decimal("2360.00"))
        self.assertEqual(inv.amount_paid, Decimal("0.00"))
        self.assertEqual(inv.outstanding_balance, Decimal("2360.00"))
        self.assertEqual(inv.status, InvoiceStatus.DRAFT)

        # 2. BILL-01: Idempotency / No duplicate invoice for same period
        inv_dup, created_dup = generate_invoice_for_subscription(sub, p_start, p_end)
        self.assertFalse(created_dup)
        self.assertEqual(inv_dup.pk, inv.pk)

        # 3. Checkpoint advancement (BILL-02)
        self.assertEqual(sub.last_billed_period_end, p_end)
        self.assertEqual(sub.next_billing_date, date(2026, 2, 1))

    def test_billing_intervals_suggested_by_plan(self):
        """Support for weekly, quarterly, yearly billing intervals (PRD §7.4)."""
        # Weekly plan
        sub_weekly = MockSubscription(id=601, user=self.customer, plan=MockPlan("Weekly Pro", "weekly"))
        p_start, p_end = compute_next_period(sub_weekly)
        self.assertEqual(p_start, date(2026, 1, 1))
        self.assertEqual(p_end, date(2026, 1, 7))

        # Quarterly plan
        sub_quarterly = MockSubscription(id=602, user=self.customer, plan=MockPlan("Quarterly Pro", "quarterly"))
        p_start, p_end = compute_next_period(sub_quarterly)
        self.assertEqual(p_start, date(2026, 1, 1))
        self.assertEqual(p_end, date(2026, 3, 31))

        # Yearly plan
        sub_yearly = MockSubscription(id=603, user=self.customer, plan=MockPlan("Annual Pro", "yearly"))
        p_start, p_end = compute_next_period(sub_yearly)
        self.assertEqual(p_start, date(2026, 1, 1))
        self.assertEqual(p_end, date(2026, 12, 31))

    def test_paused_and_expired_subscriptions(self):
        """BILL-07: Paused and expired subscriptions cannot generate invoices."""
        sub_paused = MockSubscription(id=202, user=self.customer, status="paused")
        with self.assertRaises(InvoiceNotAllowed):
            generate_invoice_for_subscription(sub_paused, date(2026, 2, 1), date(2026, 2, 28))

        sub_expired = MockSubscription(id=303, user=self.customer, expiry_date=date(2026, 1, 31))
        with self.assertRaises(InvoiceNotAllowed):
            generate_invoice_for_subscription(sub_expired, date(2026, 2, 1), date(2026, 2, 28))

    def test_payment_allocation_and_reversal(self):
        """PAY-01..PAY-05: Partial payment, overpayment rejection, and balance reversal."""
        sub = MockSubscription(id=404, user=self.customer)
        inv, _ = generate_invoice_for_subscription(sub, date(2026, 3, 1), date(2026, 3, 31))
        total = inv.total  # 2360.00

        # 1. Partial payment (1000 paid)
        inv = allocate_payment_to_invoice(inv.pk, Decimal("1000.00"))
        self.assertEqual(inv.amount_paid, Decimal("1000.00"))
        self.assertEqual(inv.outstanding_balance, total - Decimal("1000.00"))
        self.assertTrue(inv.is_partially_paid)
        self.assertEqual(inv.status, InvoiceStatus.PARTIALLY_PAID)

        # 2. Overpayment rejection (PAY-03)
        excess = inv.outstanding_balance + Decimal("1.00")
        with self.assertRaises(PaymentAllocationError):
            allocate_payment_to_invoice(inv.pk, excess)

        # 3. Pay remaining balance -> PAID
        rem = inv.outstanding_balance
        inv = allocate_payment_to_invoice(inv.pk, rem)
        self.assertEqual(inv.amount_paid, total)
        self.assertEqual(inv.outstanding_balance, Decimal("0.00"))
        self.assertEqual(inv.status, InvoiceStatus.PAID)
        self.assertFalse(inv.is_partially_paid)

        # 4. Audited reversal restores balance (PAY-04)
        inv = reverse_payment_allocation(inv.pk, Decimal("500.00"))
        self.assertEqual(inv.amount_paid, total - Decimal("500.00"))
        self.assertEqual(inv.outstanding_balance, Decimal("500.00"))
        self.assertEqual(inv.status, InvoiceStatus.PARTIALLY_PAID)

    def test_invoice_cancellation_rules(self):
        """PRD §7.9: Invoices cannot be cancelled if payments are allocated."""
        sub = MockSubscription(id=505, user=self.customer)
        inv, _ = generate_invoice_for_subscription(sub, date(2026, 4, 1), date(2026, 4, 30))

        # Can cancel when amount_paid == 0
        self.assertTrue(inv.can_cancel)

        # Allocate payment -> cannot cancel
        allocate_payment_to_invoice(inv.pk, Decimal("100.00"))
        inv.refresh_from_db()
        self.assertFalse(inv.can_cancel)
