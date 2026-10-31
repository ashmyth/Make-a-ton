import logging
from django.contrib.auth import SESSION_KEY
from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger(__name__)


def revoke_user_sessions(user) -> int:
    """Delete every live database session that belongs to ``user``."""
    user_key = str(user.pk)
    revoked = 0
    for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator():
        try:
            if session.get_decoded().get(SESSION_KEY) == user_key:
                session.delete()
                revoked += 1
        except Exception:
            pass
    return revoked
