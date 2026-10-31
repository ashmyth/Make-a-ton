import secrets
import uuid

from django.conf import settings
from django.db import IntegrityError, models, transaction

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
CODE_PREFIX = "CUST-"


def generate_customer_code() -> str:
    return CODE_PREFIX + "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


class CustomerManager(models.Manager):
    def create_with_code(self, **fields) -> "Customer":
        """Create a customer with a unique ``CUST-XXXXXXXX`` code (retries on collision)."""
        for _ in range(10):
            try:
                with transaction.atomic():
                    return self.create(customer_code=generate_customer_code(), **fields)
            except IntegrityError as exc:
                if "customer_code" not in str(exc):
                    raise
        raise RuntimeError("Could not allocate a unique customer code.")


class Customer(models.Model):
    class CustomerType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        BUSINESS = "BUSINESS", "Business"

    class PaymentTerms(models.TextChoices):
        IMMEDIATE = "IMMEDIATE", "Immediate"
        NET_15 = "NET_15", "Net 15"
        NET_30 = "NET_30", "Net 30"
        NET_60 = "NET_60", "Net 60"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_code = models.CharField(max_length=20, unique=True, editable=False)
    customer_type = models.CharField(max_length=12, choices=CustomerType.choices)
    display_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=32, blank=True)
    billing_street = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=128)
    billing_state = models.CharField(max_length=128, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=128)
    tax_identifier = models.CharField(max_length=64, blank=True)
    payment_terms = models.CharField(
        max_length=12, choices=PaymentTerms.choices, default=PaymentTerms.NET_30
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    portal_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="customer_profile",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomerManager()

    class Meta:
        db_table = "brightloop_customers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="customer_status_idx"),
            models.Index(fields=["display_name"], name="customer_name_idx"),
            models.Index(fields=["email"], name="customer_email_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.customer_code} {self.display_name}"

    @property
    def owning_customer_id(self):
        """Ownership contract used by ``CustomerDataIsolation``."""
        return self.pk
