from django.contrib import admin
from .models import Product, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('attribute_name', 'value', 'price_adjustment', 'status', 'total_unit_price')
    readonly_fields = ('total_unit_price',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'sales_price', 'cost_price', 'status', 'created_at')
    list_filter = ('status', 'type')
    search_fields = ('name', 'notes')
    inlines = [ProductVariantInline]
    actions = ['archive_products']

    @admin.action(description="Archive selected products")
    def archive_products(self, request, queryset):
        queryset.update(status='archived')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute_name', 'value', 'price_adjustment', 'total_unit_price', 'status')
    list_filter = ('status', 'attribute_name')
    search_fields = ('product__name', 'value')
    actions = ['archive_variants']

    @admin.action(description="Archive selected variants")
    def archive_variants(self, request, queryset):
        queryset.update(status='archived')



from .models import SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'billing_interval',
        'default_primary_unit_price',
        'primary_product',
        'min_quantity',
        'default_payment_terms',
        'allow_pause',
        'allow_early_closure',
        'allow_renewal',
        'auto_close_at_expiry',
        'status',
        'created_at'
    )
    list_filter = ('billing_interval', 'status', 'allow_pause', 'allow_renewal', 'auto_close_at_expiry')
    search_fields = ('name', 'default_payment_terms')
    actions = ['archive_plans']

    @admin.action(description="Archive selected plans")
    def archive_plans(self, request, queryset):
        queryset.update(status='archived')
