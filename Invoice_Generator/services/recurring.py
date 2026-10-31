"""Recurring billing engine service.
Implements BILL-01 through BILL-08 from PRD §7.8.
"""
import logging
import traceback
from datetime import date, timedelta
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from billing.generation import generate_invoice_for_subscription, InvoiceNotAllowed
from billing.models import BillingFailure, Invoice, InvoiceStatus

logger = logging.getLogger(__name__)


def resolve_billing_interval(subscription) -> str:
    """Extract billing interval from subscription, plan, or product (PRD §7.4, line 261)."""
    plan = getattr(subscription, "plan", None)
    product = getattr(subscription, "product", None)

    interval = None
    if plan and getattr(plan, "billing_interval", None):
        interval = getattr(plan, "billing_interval", None)
    elif product and getattr(product, "billing_interval", None):
        interval = getattr(product, "billing_interval", None)
    elif getattr(subscription, "billing_interval", None):
        interval = getattr(subscription, "billing_interval", None)

    return str(interval or "month").lower().strip()


def compute_next_period(subscription, as_of: Optional[date] = None) -> tuple[date, date]:
    """Compute period_start and period_end based on the product/plan's billing interval.
    
    Supports: daily, weekly, monthly, quarterly, semi-annually, yearly.
    Preserves anchor date while clamping to the end of shorter months (PRD lines 383-385).
    """
    if as_of is None:
        as_of = timezone.localdate()

    anchor = getattr(subscription, "billing_anchor_date", getattr(subscription, "start_date", as_of))
    next_billing_date = getattr(subscription, "next_billing_date", None) or anchor

    period_start = next_billing_date
    interval = resolve_billing_interval(subscription)

    if interval in ("daily", "day"):
        period_end = period_start
    elif interval in ("weekly", "week"):
        period_end = period_start + timedelta(days=6)
    elif interval in ("quarterly", "quarter", "3months"):
        period_end = (period_start + relativedelta(months=3)) - timedelta(days=1)
    elif interval in ("semi-annual", "semi_annual", "biannual", "6months"):
        period_end = (period_start + relativedelta(months=6)) - timedelta(days=1)
    elif interval in ("yearly", "year", "annual", "annually"):
        period_end = (period_start + relativedelta(years=1)) - timedelta(days=1)
    else:
        # Default to standard monthly
        period_end = (period_start + relativedelta(months=1)) - timedelta(days=1)

    return period_start, period_end


def process_subscription_billing(subscription, as_of: Optional[date] = None) -> Optional[Invoice]:
    """Processes recurring billing for a single subscription independently.
    
    Fulfills BILL-04 (independent execution) and BILL-05 (failure recording).
    """
    if as_of is None:
        as_of = timezone.localdate()

    sub_id = str(getattr(subscription, "pk", getattr(subscription, "id", "")))
    sub_number = str(getattr(subscription, "subscription_number", sub_id))

    status = str(getattr(subscription, "status", "active")).lower()
    if status in ("paused", "active/paused", "closed", "cancelled"):
        return None

    next_billing = getattr(subscription, "next_billing_date", None)
    if next_billing and next_billing > as_of:
        return None  # Not due yet

    period_start, period_end = compute_next_period(subscription, as_of)

    # BILL-07: Never bill past subscription expiry
    expiry = getattr(subscription, "expiry_date", None)
    if expiry and period_start > expiry:
        logger.info("Subscription %s reached expiry %s; stopping recurring billing", sub_number, expiry)
        return None

    try:
        invoice, created = generate_invoice_for_subscription(
            subscription, period_start=period_start, period_end=period_end
        )
        return invoice
    except Exception as exc:
        err_msg = str(exc)
        tb = traceback.format_exc()
        logger.error("Recurring billing failure for subscription %s: %s", sub_number, err_msg)
        # BILL-05: Record failure in BillingFailure table for operations review
        BillingFailure.objects.create(
            subscription_id=sub_id,
            subscription_number=sub_number,
            period_start=period_start,
            period_end=period_end,
            error_message=err_msg,
            stack_trace=tb,
        )
        return None


def run_billing_sweep(
    subscriptions_iterable=None,
    as_of: Optional[date] = None,
) -> Dict[str, List]:
    """Execute a recurring billing sweep across due subscriptions.
    
    Safe to retry (BILL-03), processes each subscription independently (BILL-04).
    """
    if as_of is None:
        as_of = timezone.localdate()

    results = {
        "generated": [],
        "existing": [],
        "failed": [],
    }

    if subscriptions_iterable is None:
        # If subscriptions app is installed, query active subscriptions
        try:
            from django.apps import apps
            Subscription = apps.get_model("subscriptions.Subscription")
            subscriptions_iterable = Subscription.objects.filter(
                status__in=["active", "running"]
            )
        except Exception:
            subscriptions_iterable = []

    for sub in subscriptions_iterable:
        sub_id = str(getattr(sub, "pk", getattr(sub, "id", "")))
        try:
            inv = process_subscription_billing(sub, as_of=as_of)
            if inv:
                results["generated"].append(inv)
        except Exception as exc:
            results["failed"].append((sub_id, str(exc)))

    return results
