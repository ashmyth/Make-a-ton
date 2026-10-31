import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from apps.access_control.roles import STAFF_ROLES, UserRole

from .fields import CIEmailField


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email or not email.strip():
            raise ValueError("Email is required.")
        extra_fields.setdefault("role", UserRole.CUSTOMER)
        user = self.model(email=normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = CIEmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CUSTOMER)
    is_active = models.BooleanField(default=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "brightloop_users"
        ordering = ["email"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=UserRole.values), name="user_role_valid"
            ),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email

    @property
    def is_staff_user(self) -> bool:
        return self.role in STAFF_ROLES

    @property
    def customer(self):
        """Linked ``Customer`` record, or ``None`` (reverse of ``Customer.portal_user``)."""
        try:
            return self.customer_profile
        except ObjectDoesNotExist:
            return None

    @property
    def customer_id(self):
        customer = self.customer
        return customer.pk if customer is not None else None

    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > timezone.now()


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "brightloop_password_reset_tokens"
        indexes = [models.Index(fields=["user", "is_used"], name="pwreset_user_used_idx")]
