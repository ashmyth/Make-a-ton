"""FEATURE 1 & PRD §7.8, §7.9, §7.12, BILL-01..08, PAY-01..05:
Invoice data structure with snapshots, immutability, and gap-safe sequencing.

Snapshots (customer, address, subscription lines, prices, tax) are copied at
issue time so historic invoices never change when catalog or profile data changes.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CONFIRMED = "confirmed", "Confirmed"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class InvoiceSequence(models.Model):
    """One row per year. Locked with select_for_update to get gap-safe numbers."""
    year = models.PositiveIntegerField(primary_key=True)
    last_number = models.PositiveIntegerField(default=0)


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=30, unique=True)

    # Optional direct payment linkage for single-payment scenarios/checkouts.
    # Per PAY-01, payments are allocated to existing invoices (Payment.invoice_id),
    # so an invoice can be created from recurring billing before any payment exists.
    payment = models.ForeignKey(
        settings.BILLING_PAYMENT_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices_legacy",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices"
    )

    # Snapshots (PRD §7.6, §7.9)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    billing_address = models.TextField(blank=True)
    subscription_id = models.CharField(max_length=64, blank=True)
    subscription_number = models.CharField(max_length=64, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    issue_date = models.DateField()
    due_date = models.DateField()
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(
        max_length=12, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT
    )

    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    # Delivery tracking (PRD §7.9, §7.14)
    pdf_path = models.CharField(max_length=255, blank=True)  # Supabase Storage path
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_attempts = models.PositiveSmallIntegerField(default=0)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )  # staff member who clicked Send

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("send_invoice", "Can send invoices to customers"),
        ]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["subscription_id", "period_start", "period_end"]),
        ]
        constraints = [
            # BILL-01: No duplicate recurring invoice per subscription and billing period
            models.UniqueConstraint(
                fields=["subscription_id", "period_start", "period_end"],
                condition=models.Q(subscription_id__gt="", period_start__isnull=False, period_end__isnull=False)
                & ~models.Q(status="cancelled"),
                name="unique_subscription_period_invoice",
            ),
        ]

    @property
    def outstanding_balance(self) -> Decimal:
        """Remaining balance on the invoice."""
        return max(Decimal("0.00"), self.total - self.amount_paid)

    @property
    def balance_due(self) -> Decimal:
        """Alias for outstanding_balance."""
        return self.outstanding_balance

    @property
    def is_partially_paid(self) -> bool:
        """PRD §7.9: Partially paid indicator."""
        return Decimal("0.00") < self.amount_paid < self.total

    @property
    def is_overdue(self) -> bool:
        """PRD §7.9: Overdue as a derived condition when due_date < today."""
        return self.outstanding_balance > Decimal("0.00") and self.due_date < timezone.localdate()

    @property
    def can_cancel(self) -> bool:
        """PRD §7.9: Prevent cancellation when payment allocations exist."""
        return self.status != InvoiceStatus.CANCELLED and self.amount_paid == Decimal("0.00")

    def __str__(self):
        return self.invoice_number


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percent
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.description} ({self.invoice.invoice_number})"


class InvoiceEmailLog(models.Model):
    """One row per send attempt. Separate from invoice status (per PRD 7.9)."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="email_logs")
    to_email = models.EmailField()
    success = models.BooleanField()
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BillingFailure(models.Model):
    """BILL-05: Record failed recurring runs, affected subscriptions, error details, and retry controls."""
    subscription_id = models.CharField(max_length=64, db_index=True)
    subscription_number = models.CharField(max_length=64, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Failure {self.subscription_number or self.subscription_id} ({self.created_at.date()})"
