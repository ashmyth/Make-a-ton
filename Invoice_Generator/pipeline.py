"""FEATURE 9: two separate steps.

 A. process_paid_payment(payment_id)   AUTOMATIC. Payment paid -> DRAFT invoice.
 B. send_invoice(invoice_id, staff)    MANUAL. Staff clicks Send in dashboard
                                       -> PDF -> Supabase copy -> email -> status update.

Email goes to invoice.customer_email (snapshot of customer's login email).
Email fail -> invoice stays Draft, failure logged, staff can click Send again.
"""
import logging

from django.db import transaction

from .models import Invoice, InvoiceStatus

from .services.emailing import send_invoice_email
from .generation import generate_invoice_for_payment
from .services.pdf import render_invoice_pdf
from .services.storage import upload_invoice_pdf

logger = logging.getLogger(__name__)


class InvoiceSendError(Exception):
    """Rule violation, message safe to show staff."""


def process_paid_payment(payment_id) -> None:
    try:
        generate_invoice_for_payment(payment_id)
    except Exception:
        logger.exception("Invoice generation failed for payment %s", payment_id)
        # retry_failed_invoices command picks up paid payments with no invoice


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
        except Exception:  # storage failure must not block email
            logger.exception("Supabase upload failed: %s", invoice.invoice_number)

        if not send_invoice_email(invoice, pdf):
            return False  # failure already logged in InvoiceEmailLog

        # Staff approved + sent -> invoice is final (no financial edits after this).
        if invoice.status == InvoiceStatus.DRAFT:
            invoice.status = (
                InvoiceStatus.PAID if invoice.balance_due <= 0 else InvoiceStatus.CONFIRMED
            )
        invoice.sent_by = staff_user
        invoice.save(update_fields=["status", "sent_by"])
        return True
