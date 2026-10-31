from datetime import date
from django.utils import timezone
from django.db import transaction
from .models import Subscription, SubscriptionStatus


@transaction.atomic
def process_subscription_expiries(as_of_date: date = None):
    """
    Automated sweep implementing PRD §7.7 and Work Division Teammate 2:
    - Scans active subscriptions where expiry_date <= as_of_date.
    - If plan.auto_close_at_expiry == True:
        Automatically closes the subscription with closure reason:
        'Term expired on {expiry_date} (auto-closed at expiry)'.
    - If plan.auto_close_at_expiry == False:
        Flags subscription as action_required = True ('Expired—action required' queue),
        which immediately halts further billing until reviewed/extended/renewed by operations.
    """
    if as_of_date is None:
        as_of_date = timezone.now().date()

    expired_candidates = Subscription.objects.select_related('plan').filter(
        status=SubscriptionStatus.ACTIVE,
        expiry_date__isnull=False,
        expiry_date__lte=as_of_date
    )

    auto_closed = []
    action_required = []

    for sub in expired_candidates:
        if sub.plan and sub.plan.auto_close_at_expiry:
            sub.close(reason=f"Term expired on {sub.expiry_date} (auto-closed at expiry)")
            auto_closed.append(sub.subscription_number)
        else:
            sub.action_required = True
            sub.action_required_reason = (
                f"Subscription expired on {sub.expiry_date} without auto-close; "
                f"renewal or closure required."
            )
            sub.save(update_fields=['action_required', 'action_required_reason', 'updated_at'])
            action_required.append(sub.subscription_number)

    return {
        'as_of_date': str(as_of_date),
        'total_evaluated': len(auto_closed) + len(action_required),
        'auto_closed_count': len(auto_closed),
        'auto_closed_subscriptions': auto_closed,
        'action_required_count': len(action_required),
        'action_required_subscriptions': action_required,
    }

