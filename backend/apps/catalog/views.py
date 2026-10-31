from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, ProductVariant, SubscriptionPlan, StatusChoices
from .serializers import (
    ProductStaffSerializer,
    ProductCustomerSerializer,
    ProductVariantSerializer,
    SubscriptionPlanStaffSerializer,
    SubscriptionPlanCustomerSerializer,
    PricingCalculationRequestSerializer
)
from .pricing import PricingService


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products in the catalog.
    Supports Create, Read, Update, and Archive.
    Prevents hard deletion to preserve historical quotations and subscriptions.
    """
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.all().prefetch_related('variants')

    def get_serializer_class(self):
        # Determine serializer based on query param or staff identity
        view_as = self.request.query_params.get('view_as')
        if view_as == 'customer':
            return ProductCustomerSerializer
        # By default for internal operations console:
        return ProductStaffSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        view_as = self.request.query_params.get('view_as')

        if view_as == 'customer':
            # Customers only ever see active products
            return queryset.filter(status=StatusChoices.ACTIVE)

        if status_param and status_param != 'all':
            return queryset.filter(status=status_param)

        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Hard deletion is explicitly blocked to protect historical audit integrity.
        Products must be archived instead.
        """
        return Response(
            {"error": "Direct deletion of products is forbidden to preserve historical financial references. Use POST /archive/ instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archives a product, making it inactive for new quotes while preserving history.
        """
        product = self.get_object()
        product.archive()
        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product variants and their price adjustments.
    """
    permission_classes = [permissions.AllowAny]
    queryset = ProductVariant.objects.all().select_related('product')
    serializer_class = ProductVariantSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id')
        status_param = self.request.query_params.get('status')

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if status_param and status_param != 'all':
            queryset = queryset.filter(status=status_param)

        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Hard deletion is blocked; variants are archived.
        """
        return Response(
            {"error": "Direct deletion of variants is forbidden. Use POST /archive/ instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archives a variant.
        """
        variant = self.get_object()
        variant.archive()
        serializer = self.get_serializer(variant)
        return Response(serializer.data, status=status.HTTP_200_OK)



class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscription plans in the catalog.
    Supports Create, Read, Update, Archive, and PRD §7.4 Pricing Preview.
    Blocks hard-deletion to preserve historical quotations and active subscription contracts.
    """
    permission_classes = [permissions.AllowAny]
    queryset = SubscriptionPlan.objects.all().select_related('primary_product')

    def get_serializer_class(self):
        if self.action == 'calculate_pricing':
            return PricingCalculationRequestSerializer
        view_as = self.request.query_params.get('view_as')
        if view_as == 'customer':
            return SubscriptionPlanCustomerSerializer
        return SubscriptionPlanStaffSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        interval_param = self.request.query_params.get('billing_interval')
        view_as = self.request.query_params.get('view_as')

        if view_as == 'customer':
            today = timezone.now().date()
            return queryset.filter(
                status=StatusChoices.ACTIVE
            ).filter(
                models.Q(availability_start_date__isnull=True) | models.Q(availability_start_date__lte=today)
            ).filter(
                models.Q(availability_end_date__isnull=True) | models.Q(availability_end_date__gte=today)
            )

        if status_param and status_param != 'all':
            queryset = queryset.filter(status=status_param)

        if interval_param:
            queryset = queryset.filter(billing_interval=interval_param)

        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Hard deletion is blocked; plans are archived to protect subscription contracts.
        """
        return Response(
            {"error": "Direct deletion of subscription plans is forbidden to preserve subscriber contracts. Use POST /archive/ instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archives a plan, preventing new quotations while keeping existing subscriptions intact.
        """
        plan = self.get_object()
        plan.archive()
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def calculate_pricing(self, request, pk=None):
        """
        Calculates commercial line pricing and recurring subtotal for a proposed quotation
        under this subscription plan, implementing PRD §7.4 pricing interpretation.
        Frontend calls this endpoint rather than computing pricing locally (TECK_STACK.md §4).
        """
        plan = self.get_object()
        serializer = PricingCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lines = data['lines']
        quote_date = data.get('quote_date')
        validate_minimums = data.get('validate_minimums', True)

        result = PricingService.calculate_plan_quote(
            plan=plan,
            lines=lines,
            quote_date=quote_date,
            validate_minimums=validate_minimums
        )
        return Response(result, status=status.HTTP_200_OK)

