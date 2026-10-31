import uuid

from django.conf import settings
from django.db import models


class AuditAction:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGIN_LOCKED = "LOGIN_LOCKED"
    LOGOUT = "LOGOUT"
    USER_REGISTERED = "USER_REGISTERED"
    PASSWORD_RESET_REQUESTED = "PASSWORD_RESET_REQUESTED"  # noqa: S105
    PASSWORD_RESET_COMPLETED = "PASSWORD_RESET_COMPLETED"  # noqa: S105
    STAFF_CREATED = "STAFF_CREATED"
    STAFF_UPDATED = "STAFF_UPDATED"
    STAFF_DEACTIVATED = "STAFF_DEACTIVATED"
    STAFF_ACTIVATED = "STAFF_ACTIVATED"
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    CUSTOMER_ARCHIVED = "CUSTOMER_ARCHIVED"
    CUSTOMER_PORTAL_LINKED = "CUSTOMER_PORTAL_LINKED"
    # Payments and Invoicing Actions
    PAYMENT_RECORDED = "PAYMENT_RECORDED"
    PAYMENT_REVERSED = "PAYMENT_REVERSED"
    INVOICE_GENERATED = "INVOICE_GENERATED"
    INVOICE_SENT = "INVOICE_SENT"
    INVOICE_CANCELLED = "INVOICE_CANCELLED"


class AppendOnlyError(Exception):
    pass


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise AppendOnlyError("Audit logs are append-only.")

    def delete(self):
        raise AppendOnlyError("Audit logs are append-only.")


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=64, db_index=True)
    entity_type = models.CharField(max_length=64, blank=True)
    entity_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = "brightloop_audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"], name="audit_timestamp_desc_idx"),
            models.Index(fields=["entity_type", "entity_id"], name="audit_entity_idx"),
        ]

    def __str__(self) -> str:
        actor_email = self.actor.email if self.actor else "system"
        return f"[{self.timestamp.isoformat()}] {actor_email} {self.action} {self.entity_type}:{self.entity_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyError("Existing audit entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError("Audit entries cannot be deleted.")
