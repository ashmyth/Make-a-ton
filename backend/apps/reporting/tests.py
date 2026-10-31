from decimal import Decimal
import uuid
from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.customers.models import Customer
from apps.subscriptions.models import Subscription, SubscriptionStatus
from apps.billing.models import Invoice, InvoiceStatus
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.payments.services import record_payment, reverse_payment
from apps.reporting.services import calculate_dashboard_metrics


class ReportingMetricCalculationTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="finance_lead@brightloop.io",
            role=UserRole.FINANCE,
        )
        self.customer = Customer.objects.create(
            customer_code="CUST-METRIC-1",
            display_name="Enterprise Systems Ltd",
            email="finance@enterprisesys.com",
        )
        today = timezone.now().date()

        # 1 Running subscription, 1 Paused subscription
        self.sub_running = Subscription.objects.create(
            subscription_number="SUB-RUN-01",
            customer=self.customer,
            plan_name="Enterprise Plan",
            start_date=today - timezone.timedelta(days=60),
            status=SubscriptionStatus.ACTIVE,
            is_paused=False,
        )
        self.sub_paused = Subscription.objects.create(
            subscription_number="SUB-PAUSE-02",
            customer=self.customer,
            plan_name="Enterprise Plan",
            start_date=today - timezone.timedelta(days=60),
            status=SubscriptionStatus.ACTIVE,
            is_paused=True,
        )

        # Invoice 1: Current, Partially Paid (Total 5,000, Paid 2,000, Outstanding 3,000)
        self.inv_current = Invoice.objects.create(
            invoice_number="INV-CURR-01",
            customer=self.customer,
            subscription=self.sub_running,
            issue_date=today - timezone.timedelta(days=5),
            due_date=today + timezone.timedelta(days=25),  # NOT overdue
            subtotal=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
            outstanding_balance=Decimal("3000.00"),
            currency="INR",
            status=InvoiceStatus.PARTIALLY_PAID,
        )
        self.payment_curr = Payment.objects.create(
            invoice=self.inv_current,
            customer=self.customer,
            recorded_by=self.staff_user,
            amount=Decimal("2000.00"),
            method=PaymentMethod.BANK_TRANSFER,
            status=PaymentStatus.SUCCEEDED,
            idempotency_key="pay-curr-1",
            paid_at=timezone.now() - timezone.timedelta(days=2),
        )

        # Invoice 2: Overdue, Unpaid (Total 3,000, Outstanding 3,000, due 10 days ago)
        self.inv_overdue = Invoice.objects.create(
            invoice_number="INV-OVERDUE-02",
            customer=self.customer,
            subscription=self.sub_running,
            issue_date=today - timezone.timedelta(days=40),
            due_date=today - timezone.timedelta(days=10),  # OVERDUE!
            subtotal=Decimal("3000.00"),
            total_amount=Decimal("3000.00"),
            outstanding_balance=Decimal("3000.00"),
            currency="INR",
            status=InvoiceStatus.CONFIRMED,
        )

    def test_seven_prd_metrics_exact_calculation(self):
        """
        Verify the 7 metrics defined in PRD §7.13:
        1. Active subscriptions = 2 (running + paused)
        2. Running subscriptions = 1 (active not paused)
        3. Billed amount = 5,000 + 3,000 = 8,000
        4. Cash collected = 2,000
        5. Outstanding balance = 3,000 + 3,000 = 6,000
        6. Overdue balance = 3,000 (from inv_overdue)
        7. Overdue invoice count = 1
        """
        metrics = calculate_dashboard_metrics()

        self.assertEqual(metrics["active_subscriptions"], 2)
        self.assertEqual(metrics["running_subscriptions"], 1)
        self.assertEqual(metrics["billed_amount"], Decimal("8000.00"))
        self.assertEqual(metrics["cash_collected"], Decimal("2000.00"))
        self.assertEqual(metrics["outstanding_balance"], Decimal("6000.00"))
        self.assertEqual(metrics["overdue_balance"], Decimal("3000.00"))
        self.assertEqual(metrics["overdue_invoice_count"], 1)

    def test_reversal_reduces_cash_collected_and_restores_balance(self):
        """Reversing a payment must immediately reflect in Cash Collected without cached drifts."""
        # Reverse the 2,000 payment
        reverse_payment(
            payment_id=self.payment_curr.id,
            reversed_by=self.staff_user,
            reason="Bank returned transaction",
        )

        metrics = calculate_dashboard_metrics()
        # Cash collected is now 0
        self.assertEqual(metrics["cash_collected"], Decimal("0.00"))
        # Outstanding balance is now 5,000 + 3,000 = 8,000
        self.assertEqual(metrics["outstanding_balance"], Decimal("8000.00"))

