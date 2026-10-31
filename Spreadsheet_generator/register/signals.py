"""Any purchase-related save -> register row updated -> xlsx rewritten. No manual entry."""
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from sales.models import Order, OrderLine, Payment

from .services import export_workbook, sync_order


def _schedule(order_id):
    # on_commit: run only after the DB transaction succeeds (admin inlines, atomic views).
    def run():
        sync_order(order_id)
        export_workbook()
    transaction.on_commit(run)


@receiver(post_save, sender=Order)
def order_saved(sender, instance, **kw):
    _schedule(instance.pk)


@receiver([post_save, post_delete], sender=OrderLine)
def line_changed(sender, instance, **kw):
    _schedule(instance.order_id)


@receiver([post_save, post_delete], sender=Payment)
def payment_changed(sender, instance, **kw):
    _schedule(instance.order_id)
