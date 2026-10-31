import secrets
import uuid
from django.conf import settings
from django.db import IntegrityError, models, transaction

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
CODE_PREFIX = "CUST-"


def generate_customer_code() -> str:
    return CODE_PREFIX + "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


class CustomerType(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", "Individual"
    BUSINESS = "BUSINESS", "Business"


class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    ARCHIVED = "ARCHIVED", "Archived"


class CustomerManager(models.Manager):
    def create_with_code(self, **fields) -> "Customer":
        """Create a customer with a unique CUST-XXXXXXXX code (retries on collision)."""
        for _ in range(10):
            try:
                with transaction.atomic():
                    return self.create(customer_code=generate_customer_code(), **fields)
            except IntegrityError as exc:
                if "customer_code" not in str(exc):
                    raise
        raise RuntimeError("Could not allocate a unique customer code.")


class Customer(models.Model):
    CustomerType = CustomerType
    Status = CustomerStatus

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

    objects = CustomerManager()

    class Meta:
        ordering = ["display_name"]

    @property
    def full_billing_address(self):
        parts = [self.billing_street, self.billing_city, self.billing_state, self.billing_postal_code, self.billing_country]
        return ", ".join([p for p in parts if p])

    @property
    def name(self) -> str:
        return self.display_name

    def __str__(self):
        return f"{self.display_name} ({self.customer_code})"
