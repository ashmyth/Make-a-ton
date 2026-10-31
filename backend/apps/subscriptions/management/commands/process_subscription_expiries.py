from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.subscriptions.services import process_subscription_expiries


class Command(BaseCommand):
    help = "Sweeps and processes expired subscriptions (auto-closes or routes to action-required queue per PRD §7.7)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--as-of',
            type=str,
            help="Target date for expiration evaluation in YYYY-MM-DD format (defaults to today)."
        )

    def handle(self, *args, **options):
        as_of_str = options.get('as_of')
        if as_of_str:
            try:
                as_of_date = datetime.strptime(as_of_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Invalid date format: {as_of_str}. Expected YYYY-MM-DD."))
                return
        else:
            as_of_date = timezone.now().date()

        self.stdout.write(f"Executing subscription expiry sweep as of {as_of_date}...")
        result = process_subscription_expiries(as_of_date=as_of_date)

        self.stdout.write(self.style.SUCCESS(
            f"Sweep complete:\n"
            f"  - Auto-closed: {result['auto_closed_count']} {result['auto_closed_subscriptions']}\n"
            f"  - Action required (billing halted): {result['action_required_count']} {result['action_required_subscriptions']}"
        ))

