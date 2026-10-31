from decimal import Decimal
from rest_framework import serializers
from .models import Product, ProductVariant, StatusChoices


class ProductVariantSerializer(serializers.ModelSerializer):
    total_unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
        help_text="Calculated unit price: sales_price + price_adjustment"
    )

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'product',
            'attribute_name',
            'value',
            'price_adjustment',
            'status',
            'total_unit_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_unit_price']

    def validate_price_adjustment(self, value):
        if not isinstance(value, Decimal):
            try:
                value = Decimal(str(value))
            except Exception:
                raise serializers.ValidationError("Invalid monetary value for price_adjustment.")
        return value


class ProductCustomerSerializer(serializers.ModelSerializer):
    """
    Customer-facing serializer.
    STRICT SECURITY RULE: cost_price is NEVER exposed to customers.
    """
    variants = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'type',
            'sales_price',
            'notes',
            'status',
            'variants',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields

    def get_variants(self, obj):
        # Customers only see active variants
        active_variants = obj.variants.filter(status=StatusChoices.ACTIVE)
        return ProductVariantSerializer(active_variants, many=True).data


class ProductStaffSerializer(serializers.ModelSerializer):
    """
    Staff-facing serializer.
    Includes internal cost_price and all variants (active & archived).
    """
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'type',
            'sales_price',
            'cost_price',
            'notes',
            'status',
            'variants',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_sales_price(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Sales price must be greater than or equal to 0.")
        return value

    def validate_cost_price(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Cost price must be greater than or equal to 0.")
        return value




from .models import SubscriptionPlan, BillingInterval


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Staff-facing serializer for managing subscription plans:
    Supports daily, weekly, monthly, and yearly billing intervals,
    minimum quantities, availability date windows, lifecycle flags
    (pause, renewal, early closure, auto-close at expiry), payment terms,
    plan status, and PRD §7.4 primary product pricing configuration.
    """
    is_currently_available = serializers.SerializerMethodField()
    primary_product_name = serializers.CharField(source='primary_product.name', read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'billing_interval',
            'min_quantity',
            'availability_start_date',
            'availability_end_date',
            'allow_pause',
            'allow_early_closure',
            'allow_renewal',
            'auto_close_at_expiry',
            'default_payment_terms',
            'primary_product',
            'primary_product_name',
            'default_primary_unit_price',
            'status',
            'is_currently_available',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_currently_available', 'primary_product_name']

    def get_is_currently_available(self, obj) -> bool:
        return obj.is_available_on()

    def validate_min_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Minimum quantity must be at least 1.")
        return value

    def validate_default_primary_unit_price(self, value):
        if value is not None and value < Decimal('0.00'):
            raise serializers.ValidationError("Default primary unit price cannot be negative.")
        return value

    def validate(self, attrs):
        start = attrs.get('availability_start_date', getattr(self.instance, 'availability_start_date', None))
        end = attrs.get('availability_end_date', getattr(self.instance, 'availability_end_date', None))
        if start and end and start > end:
            raise serializers.ValidationError({
                'availability_end_date': 'Availability end date cannot be earlier than start date.'
            })
        return attrs


SubscriptionPlanStaffSerializer = SubscriptionPlanSerializer


class SubscriptionPlanCustomerSerializer(serializers.ModelSerializer):
    """
    Customer-facing serializer for available subscription plans.
    """
    is_currently_available = serializers.SerializerMethodField()
    primary_product_name = serializers.CharField(source='primary_product.name', read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'billing_interval',
            'min_quantity',
            'availability_start_date',
            'availability_end_date',
            'allow_pause',
            'allow_early_closure',
            'allow_renewal',
            'auto_close_at_expiry',
            'default_payment_terms',
            'primary_product',
            'primary_product_name',
            'default_primary_unit_price',
            'status',
            'is_currently_available'
        ]
        read_only_fields = fields

    def get_is_currently_available(self, obj) -> bool:
        return obj.is_available_on()


class PricingLineItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(help_text="UUID of the product")
    variant_id = serializers.UUIDField(required=False, allow_null=True, help_text="Optional UUID of variant")
    quantity = serializers.IntegerField(default=1, min_value=1, help_text="Line quantity (must be >= 1)")
    is_primary = serializers.BooleanField(required=False, allow_null=True, help_text="Explicit primary product flag")


class PricingCalculationRequestSerializer(serializers.Serializer):
    lines = serializers.ListField(
        child=PricingLineItemInputSerializer(),
        allow_empty=False,
        help_text="List of product lines to price under this plan"
    )
    quote_date = serializers.DateField(required=False, allow_null=True, help_text="Optional target date for quote")
    validate_minimums = serializers.BooleanField(default=True, help_text="Whether to enforce plan min_quantity")

