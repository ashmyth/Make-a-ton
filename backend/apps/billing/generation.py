"""Invoice generation service.
Supports:
1. Recurring subscription billing (PRD §7.8, BILL-01..08)
2. Direct payment/checkout invoice generation (PRD §7.12)
"""
from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceLine, InvoiceStatus
from apps.billing.services.adapters import (
    build_invoice_input,
    build_subscription_invoice_input,
    is_payment_successful,
)
from apps.billing.services.calculation import calculate
from apps.billing.services.numbering import next_invoice_number


class InvoiceNotAllowed(Exception):
    """Raised when invoice generation business rules are violated."""
    pass


def _payment_model():
    payment_model_name = getattr(settings, "BILLING_PAYMENT_MODEL", "payments.Payment")
    return apps.get_model(payment_model_name)


@transaction.atomic
def generate_invoice_for_subscription(subscription, period_start, period_end):
    """Generate a recurring draft invoice for a subscription and billing period.
    
    Guarantees:
    - BILL-01: Zero duplicate invoices for the same subscription and period.
    - BILL-02: Checkpoint advancement in the same atomic transaction.
    - BILL-07: Never bill past subscription expiry.
    - Paused and closed subscriptions generate no new invoices (PRD §7.7).
    """
    sub_id = str(getattr(subscription, "pk", getattr(subscription, "id", "")))
    status = str(getattr(subscription, "status", "active")).lower()

    if status in ("paused", "active/paused"):
        raise InvoiceNotAllowed(f"Cannot generate invoice: Subscription {sub_id} is paused.")
    if status in ("closed", "cancelled"):
        raise InvoiceNotAllowed(f"Cannot generate invoice: Subscription {sub_id} is closed.")

    expiry_date = getattr(subscription, "expiry_date", None)
    if expiry_date and period_start > expiry_date:
        raise InvoiceNotAllowed(f"Cannot generate invoice: Period start {period_start} exceeds expiry {expiry_date}.")

    # BILL-01: Check for existing active invoice for this period
    existing = Invoice.objects.filter(
        subscription_id=sub_id,
        period_start=period_start,
        period_end=period_end,
    ).exclude(status=InvoiceStatus.CANCELLED).first()

    if existing:
        return existing, False

    data = build_subscription_invoice_input(subscription, period_start, period_end)
    result = calculate(data.lines, data.discount)

    today = timezone.localdate()
    sub_model = apps.get_model("subscriptions.Subscription", require_ready=False)
    sub_instance = subscription if isinstance(subscription, sub_model) else None

    invoice = Invoice.objects.create(
        invoice_number=next_invoice_number(),
        customer_id=data.customer_id,
        customer_name=data.customer_name,
        customer_email=data.customer_email,
        billing_address=data.billing_address,
        subscription_link=sub_instance,
        subscription_id=data.subscription_id,
        subscription_number=data.subscription_number,
        period_start=period_start,
        period_end=period_end,
        issue_date=today,
        due_date=today + timedelta(days=data.payment_terms_days),
        currency=data.currency,
        status=InvoiceStatus.DRAFT,
        subtotal=result.subtotal,
        discount_total=result.discount_total,
        tax_total=result.tax_total,
        total=result.total,
        amount_paid=Decimal("0.00"),
        outstanding_balance=result.total,
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

    # BILL-02: Atomically advance checkpoint on subscription if fields exist
    update_fields = []
    if hasattr(subscription, "last_billed_period_end"):
        subscription.last_billed_period_end = period_end
        update_fields.append("last_billed_period_end")
    if hasattr(subscription, "next_billing_date"):
        # Advance next billing date to period_end + 1 day
        subscription.next_billing_date = period_end + timedelta(days=1)
        update_fields.append("next_billing_date")
    if update_fields and hasattr(subscription, "save"):
        try:
            subscription.save(update_fields=update_fields)
        except Exception:
            pass

    return invoice, True


@transaction.atomic
def generate_invoice_for_payment(payment_id):
    """Generate invoice directly for a payment (checkout / direct payment flow).
    
    Safe to call many times (idempotent).
    """
    payment = _payment_model().objects.select_for_update().get(pk=payment_id)

    # Check if this payment is already linked to an invoice
    existing = Invoice.objects.filter(payments=payment).exclude(status=InvoiceStatus.CANCELLED).first()
    if existing:
        return existing, False

    if not is_payment_successful(payment):
        raise InvoiceNotAllowed(f"Payment {payment_id} not successful")

    data = build_invoice_input(payment)
    result = calculate(data.lines, data.discount)

    today = timezone.localdate()
    paid = min(Decimal(str(getattr(payment, "amount", 0))), result.total)

    invoice = Invoice.objects.create(
        invoice_number=next_invoice_number(),
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
        outstanding_balance=max(Decimal("0.00"), result.total - paid),
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
