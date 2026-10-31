"""Payment allocation and reversal service for invoices.
Fulfills PAY-01, PAY-03, PAY-04, PAY-05, and PRD §7.12.
"""
from decimal import Decimal
from django.db import transaction

from billing.models import Invoice, InvoiceStatus


class PaymentAllocationError(Exception):
    """Raised when payment allocation violates business rules."""
    pass


@transaction.atomic
def allocate_payment_to_invoice(
    invoice_id,
    amount: Decimal,
    payment_id: any = None,
) -> Invoice:
    """Allocates a payment amount to an invoice with atomic row-locking.
    
    Guarantees:
    - PAY-03: Overpayment protection: Rejects allocations exceeding outstanding balance.
    - PAY-05: Atomic balance & status sync (DRAFT/CONFIRMED -> PAID or partially paid).
    - Protects cancelled invoices from receiving payments.
    """
    amount = Decimal(str(amount))
    if amount <= Decimal("0.00"):
        raise PaymentAllocationError("Payment allocation amount must be positive.")

    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)

    if invoice.status == InvoiceStatus.CANCELLED:
        raise PaymentAllocationError(f"Cannot allocate payment to cancelled invoice {invoice.invoice_number}.")

    if amount > invoice.outstanding_balance:
        raise PaymentAllocationError(
            f"Overpayment rejected: payment amount ({amount}) exceeds outstanding balance ({invoice.outstanding_balance})."
        )

    invoice.amount_paid += amount

    # Update status per PRD §7.9 & PAY-05
    if invoice.outstanding_balance == Decimal("0.00"):
        invoice.status = InvoiceStatus.PAID
    elif invoice.status == InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.CONFIRMED

    invoice.save(update_fields=["amount_paid", "status", "updated_at"])
    return invoice


@transaction.atomic
def reverse_payment_allocation(
    invoice_id,
    amount: Decimal,
) -> Invoice:
    """Reverses an allocated payment amount (e.g. on refund or audited reversal per PAY-04)."""
    amount = Decimal(str(amount))
    if amount <= Decimal("0.00"):
        raise PaymentAllocationError("Reversal amount must be positive.")

    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)

    if amount > invoice.amount_paid:
        raise PaymentAllocationError(
            f"Cannot reverse {amount}; only {invoice.amount_paid} has been allocated to this invoice."
        )

    invoice.amount_paid -= amount

    # If the invoice was marked PAID, reopening a balance returns it to CONFIRMED
    if invoice.outstanding_balance > Decimal("0.00") and invoice.status == InvoiceStatus.PAID:
        invoice.status = InvoiceStatus.CONFIRMED

    invoice.save(update_fields=["amount_paid", "status", "updated_at"])
    return invoice
