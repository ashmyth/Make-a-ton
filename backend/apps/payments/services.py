from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceStatus
from apps.billing.services.allocation import (
    allocate_payment_to_invoice,
    reverse_payment_allocation,
    PaymentAllocationError,
)
from .models import Payment, PaymentStatus, PaymentMethod


@transaction.atomic
def record_payment(
    *,
    invoice_id,
    amount,
    method,
    recorded_by,
    idempotency_key,
    external_reference="",
    notes="",
    paid_at=None,
):
    """
    Atomically records and allocates a payment to an invoice.
    Enforces overpayment prevention, concurrency locking (select_for_update),
    and idempotency (PAY-01, PAY-02, PAY-03, PAY-05).
    """
    amount = Decimal(str(amount))
    if amount <= Decimal("0.00"):
        raise ValidationError("Payment amount must be strictly greater than 0.")

    # 1. Idempotency check: Replay existing payment if duplicate key (PAY-02)
    existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        if existing.invoice_id != invoice_id or existing.amount != amount:
            raise ValidationError("Idempotency key collision with different payment parameters.")
        return existing

    # 2. Lock invoice for update
    try:
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)
    except Invoice.DoesNotExist:
        raise ValidationError(f"Invoice with id '{invoice_id}' does not exist.")

    if invoice.status not in [InvoiceStatus.CONFIRMED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.DRAFT]:
        raise ValidationError(
            f"Cannot record payment against invoice {invoice.invoice_number} with status '{invoice.status}'. "
            f"Only confirmed or active invoices accept payments."
        )

    # 3. PAY-03: Overpayment check
    if amount > invoice.outstanding_balance:
        raise ValidationError(
            f"Payment allocation of {amount} exceeds remaining outstanding balance of {invoice.outstanding_balance} "
            f"on invoice {invoice.invoice_number}."
        )

    # 4. Record payment in the immutable ledger
    payment = Payment.objects.create(
        invoice=invoice,
        customer=invoice.customer,
        recorded_by=recorded_by,
        amount=amount,
        currency=invoice.currency,
        method=method,
        status=PaymentStatus.SUCCEEDED,
        idempotency_key=idempotency_key,
        external_reference=external_reference or "",
        notes=notes or "",
        paid_at=paid_at or timezone.now(),
    )

    # 5. Delegate invoice allocation and balance sync to billing service (PAY-05)
    try:
        allocate_payment_to_invoice(invoice.id, amount, payment_id=payment.id)
    except PaymentAllocationError as exc:
        raise ValidationError(str(exc))

    return payment


@transaction.atomic
def reverse_payment(*, payment_id, reversed_by, reason):
    """
    Audited payment reversal (PAY-04).
    Never hard-deletes payment records. Restores the invoice outstanding balance
    and reverts invoice status from Paid to Partially Paid or Confirmed.
    """
    if not reason or not reason.strip():
        raise ValidationError("A reversal reason must be provided for audited payment reversals.")

    try:
        payment = Payment.objects.select_for_update().get(id=payment_id)
    except Payment.DoesNotExist:
        raise ValidationError(f"Payment with id '{payment_id}' does not exist.")

    if payment.is_reversed:
        return payment  # Idempotent replay

    invoice = Invoice.objects.select_for_update().get(id=payment.invoice_id)

    payment.is_reversed = True
    payment.status = PaymentStatus.REVERSED
    payment.reversed_at = timezone.now()
    payment.reversed_by = reversed_by
    payment.reversal_reason = reason.strip()
    payment.save(update_fields=["is_reversed", "status", "reversed_at", "reversed_by", "reversal_reason"])

    # Delegate reversal to billing allocation service
    try:
        reverse_payment_allocation(invoice.id, payment.amount)
    except PaymentAllocationError as exc:
        raise ValidationError(str(exc))

    return payment
