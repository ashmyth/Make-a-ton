from django.contrib import admin

from .models import RegisterEntry


@admin.register(RegisterEntry)
class RegisterEntryAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "kind", "product", "variant",
                    "quantity", "line_total", "payment_status", "start_date", "expiry_date")
    list_filter = ("kind", "payment_status", "order_status")
    search_fields = ("order_number", "customer_name", "customer_email", "product")

    # read-only: rows come from signals only
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
