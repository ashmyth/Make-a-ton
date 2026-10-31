from typing import Any

from django.conf import settings
from django.http import HttpRequest

from .models import AuditLog


def get_client_ip(request: HttpRequest | None) -> str | None:
    """Client IP, honouring ``TRUSTED_PROXY_COUNT`` trusted reverse proxies."""
    if request is None:
        return None
    remote_addr = request.META.get("REMOTE_ADDR") or None
    proxies = settings.TRUSTED_PROXY_COUNT
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if proxies <= 0 or not forwarded:
        return remote_addr
    parts = [p.strip() for p in forwarded.split(",") if p.strip()]
    if not parts:
        return remote_addr
    return parts[-min(proxies, len(parts))]


def record_audit(
    *,
    action: str,
    actor: Any = None,
    entity_type: str = "",
    entity_id: Any = "",
    details: dict[str, Any] | None = None,
    request: HttpRequest | None = None,
) -> AuditLog:
    """Append one immutable audit entry."""
    if actor is not None and not getattr(actor, "is_authenticated", False):
        actor = None
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else "",
        details=details or {},
        ip_address=get_client_ip(request),
    )


def diff_fields(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[Any]]:
    """``{field: [old, new]}`` for every field whose value changed."""
    return {
        field: [_plain(before[field]), _plain(after[field])]
        for field in before
        if before[field] != after[field]
    }


def _plain(value: Any) -> Any:
    return value if isinstance(value, (str, int, float, bool, type(None))) else str(value)
