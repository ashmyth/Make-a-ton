from decimal import Decimal
import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model
from billing.models import Invoice, InvoiceLine, InvoiceStatus
from billing.tests.mock_payments.models import Payment
from billing.generation import generate_invoice_for_payment
from billing.pipeline import send_invoice
from billing.services.pdf import render_invoice_pdf

User = get_user_model()

@pytest.mark.django_db
def test_invoice_full_flow():
    # 1. Run migrations in-memory
    call_command("migrate", run_syncdb=True, verbosity=0)

    # 2. Setup user and staff
    user = User.objects.create_user(username="customer1", email="customer@example.com")
    staff = User.objects.create_superuser(username="admin", email="admin@example.com")

    # 3. Setup payment
    payment = Payment.objects.create(
        user=user,
        amount=Decimal("1500.00"),
        status="paid",
        customer_name="Alice Smith",
        customer_email="alice@example.com",
        billing_address="456 Tech Park",
        subscription_number="SUB-9999",
        currency="INR"
    )

    # 4. Generate invoice
    inv, created = generate_invoice_for_payment(payment.pk)
    assert created is True
    assert inv.status == InvoiceStatus.DRAFT
    assert inv.invoice_number.startswith("INV-")
    assert inv.total == Decimal("1500.00")
    assert inv.amount_paid == Decimal("1500.00")
    assert inv.balance_due == Decimal("0.00")

    # 5. Idempotent check (generating again should return same invoice, created=False)
    inv2, created2 = generate_invoice_for_payment(payment.pk)
    assert created2 is False
    assert inv2.pk == inv.pk

    # 6. PDF Rendering check
    pdf_bytes = render_invoice_pdf(inv)
    assert pdf_bytes.startswith(b"%PDF")

    # 7. Send invoice
    sent = send_invoice(inv.pk, staff_user=staff)
    assert sent is True

    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PAID
    assert inv.email_sent_at is not None
    assert inv.email_attempts == 1
    assert inv.sent_by == staff
    assert inv.email_logs.count() == 1
    assert inv.email_logs.first().success is True

