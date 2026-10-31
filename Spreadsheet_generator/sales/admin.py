from django.contrib import admin

from .models import Customer, Order, OrderLine, Payment, Plan, Product, Variant


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "product_type", "sales_price", "cost_price", "active")
    inlines = [VariantInline]


class LineInline(admin.TabularInline):
    model = OrderLine
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.action(description="Confirm selected orders")
def confirm_orders(modeladmin, request, queryset):
    for order in queryset.filter(status=Order.Status.DRAFT):
        order.status = Order.Status.CONFIRMED
        order.save()          # save() (not update()) so signals fire


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "kind", "status", "created_at")
    list_filter = ("kind", "status")
    search_fields = ("number", "customer__name", "customer__email")
    inlines = [LineInline, PaymentInline]
    actions = [confirm_orders]


admin.site.register(Customer)
admin.site.register(Plan)
