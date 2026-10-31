import uuid
from django.conf import settings
from django.db import models


class RequestType(models.TextChoices):
    PAUSE = "pause", "Pause Subscription"
    RESUME = "resume", "Resume Subscription"
    CANCEL = "cancel", "Cancel Subscription"
    RENEW = "renew", "Renew Subscription"


class RequestStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    REVIEWED = "reviewed", "Under Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class CustomerRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="portal_requests")
    subscription = models.ForeignKey(
        "subscriptions.Subscription",
        on_delete=models.CASCADE,
        related_name="customer_requests",
    )
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.SUBMITTED)
    notes = models.TextField(blank=True, help_text="Customer reasoning or instructions")
    staff_response = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_portal_requests",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.display_name} - {self.request_type} ({self.status})"
