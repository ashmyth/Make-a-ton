from django.contrib import admin
from .models import QuotationTemplate, QuotationTemplateLine, Quotation, QuotationLine


class QuotationTemplateLineInline(admin.TabularInline):
    model = QuotationTemplateLine
    extra = 1
    fields = ('product', 'variant', 'default_quantity', 'is_primary', 'sort_order')


@admin.register(QuotationTemplate)
class QuotationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan', 'validity_days', 'status', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('name', 'notes')
    inlines = [QuotationTemplateLineInline]
    actions = ['duplicate_templates', 'archive_templates']

    @admin.action(description="Duplicate selected templates")
    def duplicate_templates(self, request, queryset):
        for template in queryset:
            template.duplicate()

    @admin.action(description="Archive selected templates")
    def archive_templates(self, request, queryset):
        queryset.update(status='archived')


class QuotationLineInline(admin.TabularInline):
    model = QuotationLine
    extra = 0
    fields = ('product', 'variant', 'description', 'quantity', 'unit_price', 'line_total', 'is_primary')
    readonly_fields = ('description', 'unit_price', 'line_total')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        'quotation_number',
        'customer_id',
        'plan',
        'status',
        'issue_date',
        'expiry_date',
        'total_amount',
        'confirmed_by'
    )
    list_filter = ('status', 'plan', 'issue_date')
    search_fields = ('quotation_number', 'customer_id')
    inlines = [QuotationLineInline]
    readonly_fields = ('total_amount', 'confirmed_at')



from .models import Subscription, SubscriptionLine


class SubscriptionLineInline(admin.TabularInline):
    model = SubscriptionLine
    extra = 0
    fields = ('product', 'variant', 'description', 'quantity', 'unit_price', 'line_total', 'is_primary')
    readonly_fields = ('description', 'unit_price', 'line_total')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'subscription_number',
        'customer_id',
        'plan',
        'status',
        'operational_status',
        'start_date',
        'expiry_date',
        'next_billing_date',
        'total_recurring_amount'
    )
    list_filter = ('status', 'is_paused', 'plan', 'start_date')
    search_fields = ('subscription_number', 'customer_id_ref')
    inlines = [SubscriptionLineInline]
    readonly_fields = ('total_recurring_amount', 'created_at', 'updated_at')
