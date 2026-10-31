#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()

    from register.services import export_workbook, sync_order
    from sales.models import Order

    for oid in Order.objects.values_list("pk", flat=True):
        sync_order(oid)
    print(f"Written: {export_workbook()}")
