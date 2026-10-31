from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.customers.models import Customer
from apps.billing.models import Invoice, InvoiceStatus
from apps.payments.services import record_payment, reverse_payment
from apps.audit.models import AuditLog, AuditAction, AppendOnlyError
from apps.audit.services import record_audit

User = get_user_model()


class AuditTrailTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@brightloop.test",
            password="AdminPassword123!",
            role=UserRole.ADMINISTRATOR,
        )
        self.finance = User.objects.create_user(
            email="finance@brightloop.test",
            password="FinancePassword123!",
            role=UserRole.FINANCE,
        )
        self.customer_user = User.objects.create_user(
            email="cust@brightloop.test",
            password="CustPassword123!",
            role=UserRole.CUSTOMER,
        )
        self.customer = Customer.objects.create(
            customer_code="CUST-AUDIT01",
            display_name="Audit Test Corp",
            email="cust@brightloop.test",
            portal_user=self.customer_user,
        )
        today = timezone.now().date()
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            invoice_number="INV-AUDIT-001",
            issue_date=today,
            due_date=today + timezone.timedelta(days=30),
            subtotal=Decimal("1000.00"),
            total_amount=Decimal("1000.00"),
            outstanding_balance=Decimal("1000.00"),
            status=InvoiceStatus.CONFIRMED,
            currency="INR",
        )

    def test_model_immutability(self):
        """AuditLog entries cannot be modified or deleted via ORM."""
        entry = record_audit(action="TEST_ACTION", actor=self.admin)
        entry.action = "TAMPERED"
        with self.assertRaises(AppendOnlyError):
            entry.save()

        with self.assertRaises(AppendOnlyError):
            entry.delete()

        with self.assertRaises(AppendOnlyError):
            AuditLog.objects.filter(id=entry.id).update(action="TAMPERED")

    def test_admin_api_list_and_permissions(self):
        """Only administrators can access the audit log API."""
        record_audit(action=AuditAction.CUSTOMER_CREATED, actor=self.admin, entity_id="123")

        # Non-admin forbidden
        self.client.force_login(self.finance)
        res = self.client.get("/api/v1/audit/")
        self.assertEqual(res.status_code, 403)

        # Admin allowed
        self.client.force_login(self.admin)
        res = self.client.get("/api/v1/audit/")
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.data), 1)

    def test_payment_recording_audited(self):
        """Recording a payment writes an immutable audit log."""
        payment = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("400.00"),
            method="bank_transfer",
            recorded_by=self.finance,
            idempotency_key="idemp-audit-001",
        )

        log = AuditLog.objects.filter(
            action=AuditAction.PAYMENT_RECORDED,
            entity_id=str(payment.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.finance)
        self.assertEqual(log.details["invoice_number"], "INV-AUDIT-001")
        self.assertEqual(log.details["amount"], "400.00")

    def test_payment_reversal_audited(self):
        """Reversing a payment writes an immutable audit log."""
        payment = record_payment(
            invoice_id=self.invoice.id,
            amount=Decimal("300.00"),
            method="cash",
            recorded_by=self.finance,
            idempotency_key="idemp-audit-002",
        )

        reverse_payment(
            payment_id=payment.id,
            reversed_by=self.finance,
            reason="Customer check bounced",
        )

        log = AuditLog.objects.filter(
            action=AuditAction.PAYMENT_REVERSED,
            entity_id=str(payment.id),
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.finance)
        self.assertEqual(log.details["reason"], "Customer check bounced")
