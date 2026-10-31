from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

MONEY = dict(max_digits=12, decimal_places=2)


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    billing_address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()   # AUTH-01 normalize
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Product(models.Model):
    name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=100, blank=True)
    sales_price = models.DecimalField(validators=[MinValueValidator(0)], **MONEY)
    cost_price = models.DecimalField(validators=[MinValueValidator(0)], **MONEY)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    attribute = models.CharField(max_length=100)          # e.g. Brand
    value = models.CharField(max_length=100)              # e.g. Odoo
    price_adjustment = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("product", "attribute", "value")

    def __str__(self):
        return f"{self.product.name} / {self.attribute}: {self.value}"


class Plan(models.Model):
    class Interval(models.TextChoices):
        DAILY = "daily"
        WEEKLY = "weekly"
        MONTHLY = "monthly"
        YEARLY = "yearly"

    name = models.CharField(max_length=200)
    interval = models.CharField(max_length=10, choices=Interval.choices)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"


class Order(models.Model):
    """One purchase. kind=product -> one-time; kind=subscription -> recurring."""

    class Kind(models.TextChoices):
        PRODUCT = "product", "Product purchase"
        SUBSCRIPTION = "subscription", "Subscription"

    class Status(models.TextChoices):
        DRAFT = "draft"
        CONFIRMED = "confirmed"
        CANCELLED = "cancelled"

    number = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    kind = models.CharField(max_length=15, choices=Kind.choices, default=Kind.PRODUCT)
    plan = models.ForeignKey(Plan, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.status == self.Status.CONFIRMED and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f"ORD-{self.pk:06d}"
            super().save(update_fields=["number"])

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.kind == self.Kind.SUBSCRIPTION and not self.plan_id:
            raise ValidationError("Subscription needs a plan.")
        if self.start_date and self.expiry_date and self.start_date > self.expiry_date:
            raise ValidationError("Start date cannot be after expiry date.")

    @property
    def total(self) -> Decimal:
        agg = self.lines.aggregate(
            t=Sum(ExpressionWrapper(F("quantity") * F("unit_price"),
                                    output_field=DecimalField(max_digits=14, decimal_places=2))))
        return agg["t"] or Decimal("0.00")

    @property
    def paid(self) -> Decimal:
        return self.payments.aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

    @property
    def payment_status(self) -> str:
        total, paid = self.total, self.paid
        if paid <= 0:
            return "unpaid"
        return "paid" if paid >= total else "partial"

    def __str__(self):
        return self.number or f"Order #{self.pk}"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(Variant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    # price snapshot; auto-filled from product + variant adjustment when blank
    unit_price = models.DecimalField(null=True, blank=True, **MONEY)

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            adj = self.variant.price_adjustment if self.variant_id else Decimal("0")
            self.unit_price = self.product.sales_price + adj
        super().save(*args, **kwargs)

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price or Decimal("0")) * self.quantity


class Payment(models.Model):
    class Method(models.TextChoices):
        BANK = "bank", "Bank transfer"
        CARD = "card", "Card"
        CASH = "cash", "Cash"
        CHEQUE = "cheque", "Cheque"
        UPI = "upi", "UPI"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(validators=[MinValueValidator(Decimal("0.01"))], **MONEY)
    method = models.CharField(max_length=10, choices=Method.choices)
    paid_at = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=255, blank=True)
    external_ref = models.CharField(max_length=100, blank=True)
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.order_id:
            others = self.order.payments.exclude(pk=self.pk).aggregate(t=Sum("amount"))["t"] or 0
            if others + self.amount > self.order.total:
                raise ValidationError("Payment exceeds outstanding balance.")
