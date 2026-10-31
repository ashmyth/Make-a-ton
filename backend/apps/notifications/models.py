import uuid
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    INVOICE_SENT = "invoice_sent", "Invoice Sent"
    PAYMENT_RECEIPT = "payment_receipt", "Payment Receipt"
    PASSWORD_RESET = "password_reset", "Password Reset"
    OVERDUE_REMINDER = "overdue_reminder", "Overdue Reminder"


class NotificationStatus(models.TextChoices):
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    QUEUED = "queued", "Queued"


class EmailLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.SENT)
    payload_preview = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} ({self.status} at {self.sent_at})"
