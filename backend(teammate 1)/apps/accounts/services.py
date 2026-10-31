import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import PasswordResetToken

logger = logging.getLogger(__name__)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def revoke_user_sessions(user) -> int:
    """Delete every live database session that belongs to ``user``."""
    user_key = str(user.pk)
    revoked = 0
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        if session.get_decoded().get(SESSION_KEY) == user_key:
            session.delete()
            revoked += 1
    return revoked


def issue_password_reset(email: str) -> tuple | None:
    """Create a single-use token for an active user and email the reset link.

    Returns ``(user, token_row)`` when a token was issued, else ``None``. Callers
    must give the same response either way.
    """
    User = get_user_model()
    user = User.objects.filter(email=email, is_active=True).first()
    if user is None:
        return None

    token = secrets.token_urlsafe(32)
    with transaction.atomic():
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        row = PasswordResetToken.objects.create(
            user=user,
            token_hash=hash_token(token),
            expires_at=timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_MINUTES),
        )

    link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"
    try:
        send_mail(
            subject="Reset your Brightloop password",
            message=(
                "We received a request to reset your Brightloop password.\n\n"
                f"Use this link within {settings.PASSWORD_RESET_TOKEN_MINUTES} minutes:\n{link}\n\n"
                "If you did not request this, ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        # Response must stay neutral; the failure is logged for operators.
        logger.exception("Password reset email failed for user %s", user.pk)
    return user, row


def consume_password_reset(token: str, new_password: str):
    """Consume a reset token and set the (already validated) password.

    Returns the user, or ``None`` if the token is unknown, used, expired or the
    user is inactive.
    """
    with transaction.atomic():
        row = (
            PasswordResetToken.objects.select_for_update()
            .select_related("user")
            .filter(token_hash=hash_token(token))
            .first()
        )
        if row is None or row.is_used or row.expires_at <= timezone.now() or not row.user.is_active:
            return None
        user = row.user
        user.set_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["password", "failed_login_attempts", "locked_until", "updated_at"])
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        return user
