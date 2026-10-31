import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    CONFIRMED = "confirmed", "Confirmed"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class InvoiceSequence(models.Model):
    """One row per year. Locked with select_for_update to get gap-safe contiguous invoice numbers (BILL-02)."""
    year = models.PositiveIntegerField(primary_key=True)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Invoice Sequence"
        verbose_name_plural = "Invoice Sequences"


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)

    # CRM Customer relationship (PRD §7.2: Staff can create customers without portal user login)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    # Subscription linkage (optional snapshot and optional FK)
    subscription_id = models.CharField(max_length=64, blank=True, db_index=True)
    subscription_number = models.CharField(max_length=64, blank=True)
    subscription_link = models.ForeignKey(
        "subscriptions.Subscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )

    # Snapshots preserved at confirmation (PRD §7.6, §7.9)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    service_period_start = models.DateField(null=True, blank=True)
    service_period_end = models.DateField(null=True, blank=True)

    # Monetary fields (Exact decimal math per PRD §8)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    outstanding_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)

    # Delivery & Tracking (PRD §7.9, §7.14)
    pdf_path = models.CharField(max_length=255, blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_attempts = models.PositiveSmallIntegerField(default=0)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]
        permissions = [
            ("send_invoice", "Can send invoices to customers"),
        ]
        indexes = [
            models.Index(fields=["customer", "-created_at"]),
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["subscription_id", "period_start", "period_end"]),
        ]
        constraints = [
            # BILL-01: No duplicate recurring invoice per subscription and period
            models.UniqueConstraint(
                fields=["subscription_id", "period_start", "period_end"],
                condition=models.Q(subscription_id__gt="", period_start__isnull=False, period_end__isnull=False)
                & ~models.Q(status="cancelled"),
                name="unique_subscription_period_invoice",
            ),
        ]

    # PRD §7.9 Properties and Aliases
    @property
    def subscription(self):
        """Returns the linked Subscription instance if available."""
        return self.subscription_link

    @subscription.setter
    def subscription(self, value):
        self.subscription_link = value

    @property
    def total_amount(self) -> Decimal:
        """Alias for total to satisfy both Teammate 3 and Teammate 4 contracts."""
        return self.total

    @total_amount.setter
    def total_amount(self, value):
        self.total = Decimal(str(value))

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

    def save(self, *args, **kwargs):
        # Synchronize total, amount_paid, and outstanding_balance
        if self.total is not None and self.outstanding_balance is not None:
            if self.amount_paid == Decimal("0.00") and self.outstanding_balance < self.total:
                self.amount_paid = self.total - self.outstanding_balance
            else:
                self.outstanding_balance = max(Decimal("0.00"), self.total - self.amount_paid)

        # Auto-populate snapshot fields from customer if not provided
        if self.customer_id:
            if not self.customer_name and hasattr(self.customer, "display_name"):
                self.customer_name = self.customer.display_name
            if not self.customer_email and hasattr(self.customer, "email"):
                self.customer_email = self.customer.email
            if not self.billing_address and hasattr(self.customer, "full_billing_address"):
                self.billing_address = self.customer.full_billing_address

        # Auto-populate subscription snapshot if FK is present
        if self.subscription_link_id:
            if not self.subscription_id:
                self.subscription_id = str(self.subscription_link_id)
            if not self.subscription_number and hasattr(self.subscription_link, "subscription_number"):
                self.subscription_number = self.subscription_link.subscription_number

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name or self.customer.display_name} ({self.status}: {self.currency} {self.outstanding_balance} due)"


class InvoiceLine(models.Model):
    """Detailed itemized lines for an invoice snapshot (PRD §8)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1.000"))
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"


class InvoiceEmailLog(models.Model):
    """One row per send attempt. Separate from invoice status (PRD §7.9)."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="email_logs")
    to_email = models.EmailField()
    success = models.BooleanField()
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Email for {self.invoice.invoice_number} to {self.to_email} ({status})"


class BillingFailure(models.Model):
    """Operational failure queue for visibility and safe retries (BILL-05)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription_id = models.CharField(max_length=64, db_index=True)
    subscription_number = models.CharField(max_length=64, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Failure on Sub {self.subscription_number or self.subscription_id}: {self.error_message[:50]}"
