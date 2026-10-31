"""Two-stage invoice lifecycle pipeline:
1. process_paid_payment(payment_id) - Automatic generation upon payment
2. send_invoice(invoice_id, staff)   - Manual/Staff approval -> PDF -> Supabase/Local storage -> Email -> Status update
"""
import logging
from django.db import transaction

from apps.billing.models import Invoice, InvoiceStatus
from apps.billing.services.emailing import send_invoice_email
from apps.billing.generation import generate_invoice_for_payment
from apps.billing.services.pdf import render_invoice_pdf
from apps.billing.services.storage import upload_invoice_pdf

logger = logging.getLogger(__name__)


class InvoiceSendError(Exception):
    """Rule violation, message safe to show staff."""
    pass


def process_paid_payment(payment_id) -> None:
    try:
        generate_invoice_for_payment(payment_id)
    except Exception:
        logger.exception("Invoice generation failed for payment %s", payment_id)


def send_invoice(invoice_id, staff_user, resend: bool = False) -> bool:
    """Return True if email sent. Raise InvoiceSendError on rule violation.

    Row lock = double click / two staff cannot send twice at once.
    """
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(pk=invoice_id)

        if invoice.status == InvoiceStatus.CANCELLED:
            raise InvoiceSendError("Cancelled invoice cannot be sent.")
        if invoice.email_sent_at and not resend:
            raise InvoiceSendError("Invoice already sent. Use Resend.")

        pdf = render_invoice_pdf(invoice)

        try:
            path = upload_invoice_pdf(invoice, pdf)
            Invoice.objects.filter(pk=invoice.pk).update(pdf_path=path)
        except Exception:
            logger.exception("Storage upload failed: %s", invoice.invoice_number)

        if not send_invoice_email(invoice, pdf):
            return False

        # Staff approved + sent -> invoice is confirmed / final
        if invoice.status == InvoiceStatus.DRAFT:
            invoice.status = (
                InvoiceStatus.PAID if invoice.balance_due <= 0 else InvoiceStatus.CONFIRMED
            )
        invoice.sent_by = staff_user
        invoice.save(update_fields=["status", "sent_by"])
        return True

