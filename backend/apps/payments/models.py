import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = "bank_transfer", "Bank Transfer / NEFT / RTGS"
    CREDIT_CARD = "credit_card", "Credit Card"
    DEBIT_CARD = "debit_card", "Debit Card"
    UPI = "upi", "UPI"
    CASH = "cash", "Cash"
    CHEQUE = "cheque", "Cheque"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    REVERSED = "reversed", "Reversed"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT, related_name="payments")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="payments")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_payments")

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    status = models.CharField(max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.SUCCEEDED)

    idempotency_key = models.CharField(max_length=64, unique=True)
    external_reference = models.CharField(max_length=100, blank=True, help_text="Bank UTR, Cheque #, or Gateway Txn ID")
    notes = models.TextField(blank=True)

    paid_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    is_reversed = models.BooleanField(default=False)
    reversed_at = models.DateTimeField(null=True, blank=True)
    reversed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversed_payments",
    )
    reversal_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-paid_at", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=Decimal("0.00")),
                name="payment_amount_strictly_positive",
            )
        ]

    def __str__(self):
        state = "REVERSED" if self.is_reversed else self.status
        return f"{self.id} - {self.currency} {self.amount} for {self.invoice.invoice_number} ({state})"

