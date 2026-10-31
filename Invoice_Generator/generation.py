"""FEATURE 5: payment -> DRAFT invoice row for staff review. Idempotent.

Nothing is emailed here. Staff checks invoice in dashboard, then clicks Send.

Duplicate protection (two layers):
  1. select_for_update on payment row -> concurrent callers serialize.
  2. Invoice.payment is OneToOne -> DB rejects second invoice anyway.
"""
from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Invoice, InvoiceLine, InvoiceStatus

from .services.adapters import build_invoice_input, is_payment_successful
from .services.calculation import calculate
from .services.numbering import next_invoice_number


class InvoiceNotAllowed(Exception):
    pass


def _payment_model():
    return apps.get_model(settings.BILLING_PAYMENT_MODEL)


@transaction.atomic
def generate_invoice_for_payment(payment_id):
    """Return (invoice, created). Safe to call many times."""
    payment = _payment_model().objects.select_for_update().get(pk=payment_id)

    existing = Invoice.objects.filter(payment=payment).first()
    if existing:
        return existing, False

    if not is_payment_successful(payment):
        raise InvoiceNotAllowed(f"Payment {payment_id} not successful")

    data = build_invoice_input(payment)
    result = calculate(data.lines, data.discount)

    today = timezone.localdate()
    paid = min(Decimal(payment.amount), result.total)

    invoice = Invoice.objects.create(
        invoice_number=next_invoice_number(),
        payment=payment,
        customer_id=data.customer_id,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        billing_address=data.billing_address,
        subscription_id=data.subscription_id,
        subscription_number=data.subscription_number,
        period_start=data.period_start,
        period_end=data.period_end,
        issue_date=today,
        due_date=today + timedelta(days=data.payment_terms_days),
        currency=data.currency,
        status=InvoiceStatus.DRAFT,
        subtotal=result.subtotal,
        discount_total=result.discount_total,
        tax_total=result.tax_total,
        total=result.total,
        amount_paid=paid,
    )
    InvoiceLine.objects.bulk_create(
        InvoiceLine(
            invoice=invoice,
            description=l.description,
            quantity=l.quantity,
            unit_price=l.unit_price,
            discount_amount=l.discount_amount,
            tax_rate=l.tax_rate,
            tax_amount=l.tax_amount,
            line_total=l.line_total,
        )
        for l in result.lines
    )
    return invoice, True
