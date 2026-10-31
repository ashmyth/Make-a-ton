import uuid
from django.conf import settings
from django.db import models


class CustomerType(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", "Individual"
    BUSINESS = "BUSINESS", "Business"


class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    ARCHIVED = "ARCHIVED", "Archived"


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_code = models.CharField(max_length=32, unique=True)
    customer_type = models.CharField(max_length=20, choices=CustomerType.choices, default=CustomerType.BUSINESS)
    display_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)

    billing_street = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=30, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)

    tax_identifier = models.CharField(max_length=100, blank=True)
    payment_terms = models.CharField(max_length=50, default="NET_30")
    status = models.CharField(max_length=20, choices=CustomerStatus.choices, default=CustomerStatus.ACTIVE)

    portal_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_profile",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name"]

    @property
    def full_billing_address(self):
        parts = [self.billing_street, self.billing_city, self.billing_state, self.billing_postal_code, self.billing_country]
        return ", ".join([p for p in parts if p])

    def __str__(self):
        return f"{self.display_name} ({self.customer_code})"

