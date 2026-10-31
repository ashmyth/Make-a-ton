"""Email delivery service with PDF attachment and InvoiceEmailLog tracking.
"""
import logging
from django.conf import settings
from django.core.mail import EmailMessage

from billing.models import Invoice, InvoiceEmailLog

logger = logging.getLogger(__name__)


def send_invoice_email(invoice: Invoice, pdf_bytes: bytes) -> bool:
    """Send invoice PDF to customer email.
    
    Creates an InvoiceEmailLog entry capturing success or failure error message.
    Updates invoice.email_attempts and invoice.email_sent_at on success.
    """
    to_email = invoice.customer_email
    subject = f"Invoice {invoice.invoice_number} from {getattr(settings, 'BILLING_COMPANY_NAME', 'Brightloop')}"
    
    body = (
        f"Dear {invoice.customer_name},\n\n"
        f"Please find attached your invoice {invoice.invoice_number} "
        f"for the amount of {invoice.currency} {invoice.total}.\n\n"
        f"Due date: {invoice.due_date}\n"
        f"Outstanding balance: {invoice.currency} {invoice.balance_due}\n\n"
        f"Thank you for choosing {getattr(settings, 'BILLING_COMPANY_NAME', 'Brightloop')}.\n"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "billing@brightloop.com")
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to_email],
    )
    email.attach(f"{invoice.invoice_number}.pdf", pdf_bytes, "application/pdf")

    success = False
    error_msg = ""

    try:
        email.send(fail_silently=False)
        success = True
    except Exception as exc:
        error_msg = str(exc)
        logger.exception("Failed to send invoice email to %s: %s", to_email, exc)

    # Log the attempt in InvoiceEmailLog
    InvoiceEmailLog.objects.create(
        invoice=invoice,
        to_email=to_email,
        success=success,
        error=error_msg,
    )

    invoice.email_attempts += 1
    if success:
        from django.utils import timezone
        invoice.email_sent_at = timezone.now()
        invoice.save(update_fields=["email_attempts", "email_sent_at"])
    else:
        invoice.save(update_fields=["email_attempts"])

    return success

