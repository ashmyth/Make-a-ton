from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.billing.models import BillingFailure
from apps.billing.services.recurring import process_subscription_billing


class Command(BaseCommand):
    help = "Retry unresolved billing failures recorded in BillingFailure (BILL-05)."

    def handle(self, *args, **options):
        failures = BillingFailure.objects.filter(resolved=False)
        count = failures.count()

        if count == 0:
            self.stdout.write("No unresolved billing failures found.")
            return

        self.stdout.write(f"Attempting retry on {count} unresolved billing failure(s)...")
        Subscription = apps.get_model("subscriptions.Subscription", require_ready=False)

        resolved_count = 0
        for failure in failures:
            sub = None
            try:
                sub = Subscription.objects.filter(id=failure.subscription_id).first()
            except Exception:
                pass

            if not sub:
                self.stdout.write(self.style.WARNING(f"Subscription {failure.subscription_id} not found in DB."))
                continue

            inv = process_subscription_billing(sub)
            if inv:
                failure.resolved = True
                failure.resolved_at = timezone.now()
                failure.save(update_fields=["resolved", "resolved_at"])
                resolved_count += 1
                self.stdout.write(self.style.SUCCESS(f"Resolved failure on sub {sub.subscription_number}: Generated {inv.invoice_number}"))
            else:
                self.stdout.write(self.style.ERROR(f"Retry failed for sub {sub.subscription_number}."))

        self.stdout.write(self.style.SUCCESS(f"Retry run complete. Resolved: {resolved_count}/{count}"))
