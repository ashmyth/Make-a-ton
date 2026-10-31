"""FEATURE 1: invoice data structure.

Snapshots (customer, address, prices, tax) are copied at issue time so old
invoices never change when profile/catalog data changes.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


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

    # OneToOne = DB-level duplicate protection: one payment -> max one invoice.
    payment = models.OneToOneField(
        settings.BILLING_PAYMENT_MODEL,
        on_delete=models.PROTECT,
        related_name="invoice",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="invoices"
    )

    # Snapshots
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

    # Delivery tracking
    pdf_path = models.CharField(max_length=255, blank=True)  # Supabase Storage path
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_attempts = models.PositiveSmallIntegerField(default=0)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )  # staff member who clicked Send

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [("send_invoice", "Can send invoices to customers")]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["status", "due_date"]),
        ]

    @property
    def balance_due(self) -> Decimal:
        return self.total - self.amount_paid

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


class InvoiceEmailLog(models.Model):
    """One row per send attempt. Separate from invoice status (per PRD 7.9)."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="email_logs")
    to_email = models.EmailField()
    success = models.BooleanField()
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
