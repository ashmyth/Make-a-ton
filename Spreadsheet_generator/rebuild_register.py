from django.core.management.base import BaseCommand

from register.services import export_workbook, sync_order
from sales.models import Order


class Command(BaseCommand):
    help = "Backfill register from all orders and rewrite the xlsx."

    def handle(self, *args, **opts):
        for oid in Order.objects.values_list("pk", flat=True):
            sync_order(oid)
        self.stdout.write(self.style.SUCCESS(f"Written: {export_workbook()}"))
