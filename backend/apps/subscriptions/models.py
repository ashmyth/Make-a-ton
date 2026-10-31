import uuid
from decimal import Decimal
from datetime import timedelta
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Product, ProductVariant, SubscriptionPlan, StatusChoices


class QuotationStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    SENT = 'sent', 'Sent'
    REVIEWED = 'reviewed', 'Reviewed'
    CONFIRMED = 'confirmed', 'Confirmed'
    EXPIRED = 'expired', 'Expired'
    CANCELLED = 'cancelled', 'Cancelled'


class SubscriptionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    QUOTATION = "quotation", "Quotation"
    CONFIRMED = "confirmed", "Confirmed"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    CLOSED = "closed", "Closed"


class BillingInterval(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class OperationalStatus(models.TextChoices):
    RUNNING = 'running', 'Running'
    PAUSED = 'paused', 'Paused'


class QuotationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Template display name")
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='quotation_templates',
        help_text="Default subscription plan applicable to this template"
    )
    validity_days = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Validity duration in days for quotations created from this template"
    )
    notes = models.TextField(blank=True, null=True, help_text="Template description or internal notes")
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        help_text="Active or Archived"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Quotation Template'
        verbose_name_plural = 'Quotation Templates'

    def __str__(self):
        return f"{self.name} ({self.plan.name})"

    def archive(self):
        self.status = StatusChoices.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])

    @transaction.atomic
    def duplicate(self, new_name=None):
        if not new_name:
            base_name = f"{self.name} (Copy)"
            candidate_name = base_name
            counter = 1
            while QuotationTemplate.objects.filter(name=candidate_name).exists():
                candidate_name = f"{base_name} {counter}"
                counter += 1
            new_name = candidate_name

        new_template = QuotationTemplate.objects.create(
            name=new_name,
            plan=self.plan,
            validity_days=self.validity_days,
            notes=self.notes,
            status=StatusChoices.ACTIVE
        )

        for line in self.lines.all():
            QuotationTemplateLine.objects.create(
                template=new_template,
                product=line.product,
                variant=line.variant,
                default_quantity=line.default_quantity,
                is_primary=line.is_primary,
                sort_order=line.sort_order
            )

        return new_template


class QuotationTemplateLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        QuotationTemplate,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent quotation template"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='template_lines',
        help_text="Product for this line"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='template_lines',
        help_text="Specific product variant (optional)"
    )
    default_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Default line item quantity"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="True if this represents the primary plan service (for PRD §7.4 plan default price)"
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Quotation Template Line'
        verbose_name_plural = 'Quotation Template Lines'

    def clean(self):
        super().clean()
        if self.variant and self.variant.product_id != self.product_id:
            raise ValidationError({
                'variant': 'The selected variant does not belong to the selected product.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Quotation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quotation_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique commercial quotation identifier (e.g. QT-2026-0001)"
    )
    customer_id = models.CharField(
        max_length=100,
        help_text="Customer ID (integrates with Teammate 1 customer foundation)"
    )
    template = models.ForeignKey(
        QuotationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        help_text="Original template from which this quotation was created (optional)"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='quotations',
        help_text="Subscription plan governing terms and billing interval"
    )
    status = models.CharField(
        max_length=20,
        choices=QuotationStatus.choices,
        default=QuotationStatus.DRAFT,
        help_text="Current quotation workflow status"
    )
    issue_date = models.DateField(default=timezone.now, help_text="Date when quotation was issued")
    expiry_date = models.DateField(help_text="Calculated expiration date: issue_date + validity_days")
    payment_terms = models.CharField(max_length=100, blank=True, null=True, help_text="Agreed payment terms")
    notes = models.TextField(blank=True, null=True, help_text="Commercial notes or scope description")
    confirmed_by = models.CharField(max_length=150, null=True, blank=True, help_text="Staff identity who confirmed the quote")
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="Exact timestamp of commercial confirmation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quotation'
        verbose_name_plural = 'Quotations'

    def __str__(self):
        return f"{self.quotation_number} - Customer {self.customer_id} ({self.status})"

    @property
    def is_expired(self) -> bool:
        if self.status == QuotationStatus.CONFIRMED:
            return False
        return timezone.now().date() > self.expiry_date

    @property
    def total_amount(self) -> Decimal:
        return sum((line.line_total for line in self.lines.all()), Decimal('0.00'))

    def extend_validity(self, additional_days: int):
        if additional_days < 1:
            raise ValidationError("Additional validity days must be at least 1.")
        base_date = max(timezone.now().date(), self.expiry_date)
        self.expiry_date = base_date + timedelta(days=additional_days)
        if self.status == QuotationStatus.EXPIRED:
            self.status = QuotationStatus.REVIEWED
        self.save(update_fields=['expiry_date', 'status', 'updated_at'])

    def confirm(self, confirmed_by_user="Staff"):
        if self.status == QuotationStatus.CONFIRMED:
            raise ValidationError("This quotation is already confirmed.")

        if self.is_expired:
            self.status = QuotationStatus.EXPIRED
            self.save(update_fields=['status', 'updated_at'])
            raise ValidationError(
                f"Quotation {self.quotation_number} expired on {self.expiry_date} and cannot be confirmed unless extended or reissued."
            )

        primary_quantity = sum(
            (line.quantity for line in self.lines.filter(is_primary=True)),
            0
        )
        if primary_quantity < self.plan.min_quantity:
            raise ValidationError(
                f"Plan '{self.plan.name}' requires a minimum quantity of {self.plan.min_quantity}. Current primary quantity: {primary_quantity}."
            )

        if not self.lines.exists():
            raise ValidationError("Quotation must have at least one product line before confirmation.")

        self.status = QuotationStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.confirmed_by = confirmed_by_user
        self.save(update_fields=['status', 'confirmed_at', 'confirmed_by', 'updated_at'])

    def send_to_customer(self):
        if self.status != QuotationStatus.DRAFT:
            raise ValidationError(f"Cannot send quotation in '{self.status}' status. Must be draft.")
        self.status = QuotationStatus.SENT
        self.save(update_fields=['status', 'updated_at'])

    def mark_reviewed(self):
        if self.status not in [QuotationStatus.DRAFT, QuotationStatus.SENT]:
            raise ValidationError(f"Cannot mark quotation as reviewed from '{self.status}' status.")
        self.status = QuotationStatus.REVIEWED
        self.save(update_fields=['status', 'updated_at'])

    def cancel(self, reason=None):
        if self.status == QuotationStatus.CONFIRMED:
            raise ValidationError("Confirmed quotations cannot be cancelled.")
        self.status = QuotationStatus.CANCELLED
        if reason:
            self.notes = f"{self.notes or ''}\nCancellation Reason: {reason}".strip()
        self.save(update_fields=['status', 'notes', 'updated_at'])


class QuotationLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent quotation"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='quotation_lines',
        help_text="Referenced product"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='quotation_lines',
        help_text="Referenced variant (optional)"
    )
    description = models.CharField(
        max_length=255,
        help_text="Frozen snapshot description of product and variant"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Agreed billable quantity"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Frozen commercial unit price snapshot (PRD §7.4 resolved)"
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Frozen line total: quantity * unit_price"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Designates the primary service line"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Quotation Line'
        verbose_name_plural = 'Quotation Lines'

    @classmethod
    def resolve_unit_price(cls, plan: SubscriptionPlan, product: Product, variant: ProductVariant = None, is_primary: bool = False) -> Decimal:
        if is_primary and plan.default_primary_unit_price is not None:
            base = plan.default_primary_unit_price
        else:
            base = product.sales_price

        adjustment = variant.price_adjustment if variant else Decimal('0.00')
        return base + adjustment

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """
    Represents an active recurring commercial subscription.
    Integrated with Teammate 1 Customers and Teammate 4 Portal.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="subscriptions",
        null=True,
        blank=True
    )
    customer_id_ref = models.CharField(max_length=100, blank=True, help_text="Customer ID string from T1")
    quotation = models.OneToOneField(
        Quotation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    plan_name = models.CharField(max_length=150, blank=True)
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )
    is_paused = models.BooleanField(default=False)
    currency = models.CharField(max_length=3, default="INR")

    start_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    billing_anchor_date = models.DateField(null=True, blank=True)
    next_billing_date = models.DateField(null=True, blank=True)
    last_billed_period_end = models.DateField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, default="Immediate")

    pause_date = models.DateField(null=True, blank=True)
    pause_reason = models.TextField(blank=True, null=True)
    resume_date = models.DateField(null=True, blank=True)
    closure_date = models.DateField(null=True, blank=True)
    closure_reason = models.TextField(blank=True, null=True)

    predecessor = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='successor'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __init__(self, *args, **kwargs):
        if 'customer_id' in kwargs:
            val = kwargs.pop('customer_id')
            if val is not None:
                is_uuid = False
                if isinstance(val, uuid.UUID):
                    is_uuid = True
                else:
                    try:
                        uuid.UUID(str(val))
                        is_uuid = True
                    except (ValueError, TypeError):
                        is_uuid = False

                if is_uuid:
                    kwargs['customer_id'] = val
                else:
                    kwargs['customer_id_ref'] = str(val)
                    kwargs['customer'] = None
        super().__init__(*args, **kwargs)

    def __str__(self):
        cust = self.customer.display_name if self.customer else self.customer_id_ref
        return f"{self.subscription_number} - {cust} ({self.status})"

    @property
    def customer_id(self):
        if self.customer:
            return str(self.customer.id)
        return self.customer_id_ref

    @property
    def operational_status(self):
        if self.is_paused or self.status == SubscriptionStatus.PAUSED:
            return "paused"
        return "running"

    @operational_status.setter
    def operational_status(self, value):
        val = str(value).lower()
        if val == "paused":
            self.is_paused = True
            if self.status == SubscriptionStatus.ACTIVE:
                self.status = SubscriptionStatus.PAUSED
        else:
            self.is_paused = False
            if self.status == SubscriptionStatus.PAUSED:
                self.status = SubscriptionStatus.ACTIVE

    @property
    def total_recurring_amount(self) -> Decimal:
        return sum((line.line_total for line in self.lines.all()), Decimal('0.00'))

    def pause(self, reason=None):
        if self.status != SubscriptionStatus.ACTIVE and self.status != SubscriptionStatus.PAUSED:
            raise ValidationError(f"Only active subscriptions can be paused. Current status is '{self.status}'.")
        if self.is_paused or self.status == SubscriptionStatus.PAUSED:
            raise ValidationError("Subscription is already paused.")
        if self.plan and not self.plan.allow_pause:
            raise ValidationError(f"Plan '{self.plan.name}' does not permit pausing.")

        self.is_paused = True
        self.status = SubscriptionStatus.PAUSED
        self.pause_date = timezone.now().date()
        self.pause_reason = reason or "Customer requested operational pause."
        self.version += 1
        self.save()

    def resume(self):
        if not self.is_paused and self.status != SubscriptionStatus.PAUSED:
            raise ValidationError("Subscription is not paused.")

        self.is_paused = False
        self.status = SubscriptionStatus.ACTIVE
        self.resume_date = timezone.now().date()
        self.version += 1
        self.save()

    def close(self, reason=None, early: bool = False):
        if self.status == SubscriptionStatus.CLOSED:
            raise ValidationError("Subscription is already closed.")

        today = timezone.now().date()
        is_early = self.expiry_date and today < self.expiry_date
        if is_early and self.plan and not self.plan.allow_early_closure and not early:
            raise ValidationError(f"Plan '{self.plan.name}' does not permit early closure before term expiry.")

        self.status = SubscriptionStatus.CLOSED
        self.closure_date = today
        self.closure_reason = reason or ("Early cancellation" if is_early else "Term expired")
        self.version += 1
        self.save()

    @transaction.atomic
    def renew(self, new_start_date=None, new_expiry_date=None):
        if self.plan and not self.plan.allow_renewal:
            raise ValidationError(f"Plan '{self.plan.name}' does not permit renewals.")
        if hasattr(self, 'successor') and self.successor is not None:
            raise ValidationError(f"Subscription {self.subscription_number} has already been renewed into {self.successor.subscription_number}.")

        today = timezone.now().date()
        effective_start = new_start_date or (self.expiry_date or today)

        year = effective_start.year
        count = Subscription.objects.filter(start_date__year=year).count() + 1
        sub_number = f"SUB-{year}-{count:04d}"
        while Subscription.objects.filter(subscription_number=sub_number).exists():
            count += 1
            sub_number = f"SUB-{year}-{count:04d}"

        successor = Subscription.objects.create(
            subscription_number=sub_number,
            customer=self.customer,
            customer_id_ref=self.customer_id_ref,
            plan=self.plan,
            plan_name=self.plan_name,
            billing_interval=self.billing_interval,
            status=SubscriptionStatus.ACTIVE,
            is_paused=False,
            start_date=effective_start,
            expiry_date=new_expiry_date,
            billing_anchor_date=self.billing_anchor_date or effective_start,
            next_billing_date=effective_start,
            payment_terms=self.payment_terms,
            predecessor=self
        )

        for line in self.lines.all():
            SubscriptionLine.objects.create(
                subscription=successor,
                product=line.product,
                variant=line.variant,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                is_primary=line.is_primary,
                sort_order=line.sort_order
            )

        self.status = SubscriptionStatus.CLOSED
        self.closure_date = effective_start
        self.closure_reason = f"Renewed into successor subscription {sub_number}"
        self.save()

        return successor


class SubscriptionLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent subscription"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='subscription_lines',
        help_text="Referenced product"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subscription_lines',
        help_text="Referenced variant (optional)"
    )
    description = models.CharField(
        max_length=255,
        help_text="Frozen snapshot product and variant description"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Subscribed recurring quantity"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Frozen agreed recurring unit price"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Designates the primary service line"
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        verbose_name = 'Subscription Line'
        verbose_name_plural = 'Subscription Lines'

    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.description} x {self.quantity} @ {self.unit_price}"
