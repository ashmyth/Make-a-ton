from django.db import models
from django.conf import settings

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=20, default="paid")
    customer_name = models.CharField(max_length=255, default="John Doe")
    customer_email = models.EmailField(default="john@example.com")
    billing_address = models.TextField(blank=True, default="123 Street")
    subscription_id = models.CharField(max_length=64, default="SUB-101")
    subscription_number = models.CharField(max_length=64, default="SUB-101")
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="INR")

