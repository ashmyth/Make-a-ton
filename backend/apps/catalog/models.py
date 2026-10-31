import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class StatusChoices(models.TextChoices):
    ACTIVE = 'active', 'Active'
    ARCHIVED = 'archived', 'Archived'


class Product(models.Model):
    """
    Represents a sellable product in the Brightloop catalog.
    Historical references are preserved: products are archived, never hard-deleted.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Product display name")
    type = models.CharField(max_length=100, blank=True, null=True, help_text="Product category/type (e.g. Software, Service)")
    sales_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Base sales price offered to customers"
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Internal cost price (hidden from customer views)"
    )
    notes = models.TextField(blank=True, null=True, help_text="Internal notes")
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
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.name} ({self.status})"

    def archive(self):
        """Archives the product so it is inactive but retains historical references."""
        self.status = StatusChoices.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])


class ProductVariant(models.Model):
    """
    Represents a variant of a product (e.g., Brand=Odoo) with a price adjustment.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        help_text="Parent product this variant belongs to"
    )
    attribute_name = models.CharField(max_length=100, help_text="Attribute name (e.g., Brand, Tier, Color)")
    value = models.CharField(max_length=100, help_text="Attribute value (e.g., Odoo, Enterprise, Blue)")
    price_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Adjustment added to base product sales price (can be positive, zero, or negative)"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        help_text="Active or Archived"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['attribute_name', 'value']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'attribute_name', 'value'],
                name='unique_product_variant_combination'
            )
        ]
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'

    def __str__(self):
        return f"{self.product.name} - {self.attribute_name}: {self.value} ({'+' if self.price_adjustment >= 0 else ''}{self.price_adjustment})"

    @property
    def total_unit_price(self) -> Decimal:
        """Calculates effective base unit price (Base sales price + variant adjustment)."""
        return self.product.sales_price + self.price_adjustment

    def archive(self):
        """Archives the variant."""
        self.status = StatusChoices.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])



class BillingInterval(models.TextChoices):
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    YEARLY = 'yearly', 'Yearly'


BillingIntervalChoices = BillingInterval


class SubscriptionPlan(models.Model):
    """
    Represents a subscription billing plan with commercial rules, billing intervals,
    availability dates, lifecycle policies, and PRD §7.4 pricing configuration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Plan display name")
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        help_text="Recurring billing frequency: daily, weekly, monthly, or yearly"
    )
    min_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Minimum required quantity of primary product to activate this plan"
    )
    availability_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when this plan becomes available for quotations (optional)"
    )
    availability_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date after which this plan cannot be selected for new quotations (optional)"
    )
    allow_pause = models.BooleanField(
        default=False,
        help_text="Whether subscriptions under this plan permit operational pausing"
    )
    allow_early_closure = models.BooleanField(
        default=False,
        help_text="Whether subscriptions under this plan permit early termination before term expiry"
    )
    allow_renewal = models.BooleanField(
        default=True,
        help_text="Whether subscriptions under this plan can be renewed into successor subscriptions"
    )
    auto_close_at_expiry = models.BooleanField(
        default=True,
        help_text="Whether subscriptions automatically close when reaching expiration date"
    )
    default_payment_terms = models.CharField(
        max_length=100,
        default="Immediate",
        help_text="Default payment terms (e.g. Immediate, Net 15, Net 30)"
    )
    primary_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_plans',
        help_text="Designated primary product whose base sales price is overridden by this plan (PRD §7.4)"
    )
    default_primary_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Optional default price for primary product (overrides primary product base sales price per PRD §7.4)"
    )
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
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} ({self.billing_interval})"

    @property
    def price(self) -> Decimal | None:
        """Alias for default_primary_unit_price for convenient access."""
        return self.default_primary_unit_price

    @price.setter
    def price(self, value):
        self.default_primary_unit_price = value

    @property
    def availability_start(self):
        return self.availability_start_date

    @availability_start.setter
    def availability_start(self, value):
        self.availability_start_date = value

    @property
    def availability_end(self):
        return self.availability_end_date

    @availability_end.setter
    def availability_end(self, value):
        self.availability_end_date = value

    @property
    def payment_terms(self):
        return self.default_payment_terms

    @payment_terms.setter
    def payment_terms(self, value):
        self.default_payment_terms = value

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.availability_start_date and self.availability_end_date:
            if self.availability_start_date > self.availability_end_date:
                raise ValidationError({
                    'availability_end_date': 'Availability end date cannot be earlier than start date.'
                })
        if self.min_quantity is not None and self.min_quantity < 1:
            raise ValidationError({
                'min_quantity': 'Minimum quantity must be at least 1.'
            })
        if self.default_primary_unit_price is not None and self.default_primary_unit_price < Decimal('0.00'):
            raise ValidationError({
                'default_primary_unit_price': 'Price cannot be negative.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def archive(self):
        """Archives the plan to prevent new quotations while preserving existing subscriptions."""
        self.status = StatusChoices.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])

    def is_available_on(self, target_date=None) -> bool:
        """Dynamically verifies if the plan is eligible for new quotations on a given date."""
        from django.utils import timezone
        if target_date is None:
            target_date = timezone.now().date()
        if self.status != StatusChoices.ACTIVE:
            return False
        if self.availability_start_date and target_date < self.availability_start_date:
            return False
        if self.availability_end_date and target_date > self.availability_end_date:
            return False
        return True

    def is_available(self, target_date=None) -> bool:
        """Alias for is_available_on."""
        return self.is_available_on(target_date)

    def calculate_unit_price(self, product, variant=None, is_primary=None) -> Decimal:
        """
        Calculates the effective recurring unit price for a product line under this plan,
        strictly following the agreed pricing interpretation from PRD §7.4:
        - Subscription line unit prices are the source of recurring charges.
        - A plan may define a default per-unit price for a designated primary product.
        - That default replaces the primary product's base price before variant adjustments.
        - Add-ons use their own product prices.
        - The plan price is not added again as a separate charge.
        """
        from .pricing import PricingService
        return PricingService.calculate_line_unit_price(
            plan=self,
            product=product,
            variant=variant,
            is_primary=is_primary
        )


Plan = SubscriptionPlan
