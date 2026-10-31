from django.db import models


class RegisterEntry(models.Model):
    """Denormalised snapshot row = one spreadsheet row. Kept in sync by signals."""

    order_line = models.OneToOneField("sales.OrderLine", on_delete=models.CASCADE,
                                      related_name="register_entry")
    order_id_ref = models.BigIntegerField(db_index=True)
    order_number = models.CharField(max_length=20, db_index=True)
    purchase_date = models.DateTimeField(null=True)
    order_status = models.CharField(max_length=10)
    kind = models.CharField(max_length=15, db_index=True)

    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30, blank=True)

    product = models.CharField(max_length=200)
    variant = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    plan = models.CharField(max_length=200, blank=True)
    billing_interval = models.CharField(max_length=10, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    order_total = models.DecimalField(max_digits=14, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2)
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    payment_status = models.CharField(max_length=10)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-purchase_date", "order_number"]
        verbose_name_plural = "register entries"
