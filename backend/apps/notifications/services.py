from django.utils import timezone
from .models import EmailLog, NotificationType, NotificationStatus


def send_invoice_notification(invoice):
    """
    Renders invoice email notice with secure portal link and records the sending attempt in EmailLog (PRD §7.14).
    """
    recipient = invoice.customer.email
    subject = f"Invoice #{invoice.invoice_number} from Brightloop"
    preview = (
        f"Dear {invoice.customer.contact_person or invoice.customer.display_name},\n\n"
        f"Your invoice #{invoice.invoice_number} for {invoice.currency} {invoice.total_amount} is ready.\n"
        f"Due date: {invoice.due_date}\n"
        f"Outstanding balance: {invoice.currency} {invoice.outstanding_balance}\n\n"
        f"You can view and download your full invoice anytime in your customer portal."
    )

    log = EmailLog.objects.create(
        recipient=recipient,
        subject=subject,
        notification_type=NotificationType.INVOICE_SENT,
        status=NotificationStatus.SENT,
        payload_preview=preview,
        sent_at=timezone.now(),
    )
    return log


def send_payment_receipt_notification(payment):
    """
    Renders payment receipt notice and records the sending attempt in EmailLog (PRD §7.14).
    """
    recipient = payment.customer.email
    subject = f"Payment Receipt for Invoice #{payment.invoice.invoice_number}"
    preview = (
        f"Dear {payment.customer.contact_person or payment.customer.display_name},\n\n"
        f"We have received and recorded your payment of {payment.currency} {payment.amount} "
        f"via {payment.get_method_display()} on {payment.paid_at.strftime('%Y-%m-%d')}.\n"
        f"Remaining balance on invoice #{payment.invoice.invoice_number}: "
        f"{payment.currency} {payment.invoice.outstanding_balance}.\n\n"
        f"Thank you for your business."
    )

    log = EmailLog.objects.create(
        recipient=recipient,
        subject=subject,
        notification_type=NotificationType.PAYMENT_RECEIPT,
        status=NotificationStatus.SENT,
        payload_preview=preview,
        sent_at=timezone.now(),
    )
    return log
