from decimal import Decimal
import uuid
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.accounts.models import User, UserRole
from apps.customers.models import Customer
from apps.billing.models import Invoice, InvoiceStatus
from apps.payments.models import Payment, PaymentStatus, PaymentMethod
from apps.payments.services import record_payment, reverse_payment


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            email="finance@brightloop.io",
            password="SecurePassword@123",
            role=UserRole.FINANCE,
            first_name="Finance",
            last_name="Officer",
        )
        self.customer = Customer.objects.create(
            customer_code="CUST-001",
            display_name="Acme Corp",
            contact_person="Alice",
            email="alice@acme.com",
            phone="+919876543210",
            billing_street="10 Tech Park",
            billing_city="Bengaluru",
            billing_state="Karnataka",
            billing_postal_code="560100",
            billing_country="India",
        )
        today = timezone.now().date()
        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-001",
            customer=self.customer,
            issue_date=today,
            due_date=today + timezone.timedelta(days=30),
            subtotal=Decimal("1000.00"),
            total_amount=Decimal("1000.00"),
            outstanding_balance=Decimal("1000.00"),
            currency="INR",
            status=InvoiceStatus.CONFIRMED,
        )

    def test_prd_acceptance_example_partial_and_full_payment(self):
        """
        PRD §7.12 Acceptance Example:
        For an invoice total of 1,000, a payment of 400 leaves 600 outstanding (partially paid).
        A second payment of 600 marks the invoice Paid.
        """
        p1 = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("400.00"),
            method=PaymentMethod.BANK_TRANSFER,
            recorded_by=self.staff_user,
            idempotency_key="key-part-1",
            external_reference="UTR-12345",
        )
        self.invoice.refresh_from_db()
        self.assertEqual(p1.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(self.invoice.outstanding_balance, Decimal("600.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PARTIALLY_PAID)

        p2 = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("600.00"),
            method=PaymentMethod.UPI,
            recorded_by=self.staff_user,
            idempotency_key="key-part-2",
            external_reference="UPI-67890",
        )
        self.invoice.refresh_from_db()
        self.assertEqual(p2.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(self.invoice.outstanding_balance, Decimal("0.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)

    def test_overpayment_protection_rejected(self):
        """
        PRD PAY-03:
        Payment exceeding the invoice's remaining balance must raise a ValidationError.
        """
        with self.assertRaises(ValidationError) as ctx:
            record_payment(
                invoice_id=self.invoice.id,
                amount=Decimal("1000.01"),
                method=PaymentMethod.CREDIT_CARD,
                recorded_by=self.staff_user,
                idempotency_key="key-overpay",
            )
        self.assertIn("exceeds remaining outstanding balance", str(ctx.exception))
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.outstanding_balance, Decimal("1000.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.CONFIRMED)

    def test_idempotent_recording_prevents_duplicate_payments(self):
        """
        PRD PAY-02:
        Submitting with the same idempotency_key returns the existing payment without duplicate balance deduction.
        """
        p1 = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("300.00"),
            method=PaymentMethod.BANK_TRANSFER,
            recorded_by=self.staff_user,
            idempotency_key="same-key-uuid",
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.outstanding_balance, Decimal("700.00"))

        # Re-send identical request
        p2 = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("300.00"),
            method=PaymentMethod.BANK_TRANSFER,
            recorded_by=self.staff_user,
            idempotency_key="same-key-uuid",
        )
        self.assertEqual(p1.id, p2.id)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.outstanding_balance, Decimal("700.00"))
        self.assertEqual(Payment.objects.filter(invoice=self.invoice).count(), 1)

    def test_audited_reversal_restores_balance_and_status(self):
        """
        PRD PAY-04:
        Reversing a payment restores the invoice balance and status.
        """
        p = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("400.00"),
            method=PaymentMethod.CHEQUE,
            recorded_by=self.staff_user,
            idempotency_key="reversal-key-1",
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.outstanding_balance, Decimal("600.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.PARTIALLY_PAID)

        # Reverse payment
        reversed_p = reverse_payment(
            payment_id=p.id,
            reversed_by=self.staff_user,
            reason="Cheque bounced due to signature mismatch",
        )
        self.assertTrue(reversed_p.is_reversed)
        self.assertEqual(reversed_p.status, PaymentStatus.REVERSED)
        self.assertEqual(reversed_p.reversal_reason, "Cheque bounced due to signature mismatch")

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.outstanding_balance, Decimal("1000.00"))
        self.assertEqual(self.invoice.status, InvoiceStatus.CONFIRMED)
