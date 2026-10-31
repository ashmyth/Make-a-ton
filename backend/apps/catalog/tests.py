from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Product, ProductVariant, StatusChoices


class ProductCatalogModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="ERP Suite",
            type="Software",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("400.00"),
            notes="Core enterprise software"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            attribute_name="Brand",
            value="Odoo",
            price_adjustment=Decimal("560.00")
        )

    def test_product_creation_and_defaults(self):
        """Verifies product is created with active status and correct fields."""
        self.assertEqual(self.product.name, "ERP Suite")
        self.assertEqual(self.product.status, StatusChoices.ACTIVE)
        self.assertEqual(self.product.sales_price, Decimal("1000.00"))
        self.assertEqual(self.product.cost_price, Decimal("400.00"))

    def test_variant_price_calculation(self):
        """
        PRD Acceptance example:
        Base price 1,000 + Odoo variant adjustment 560 = 1,560 unit price.
        """
        self.assertEqual(self.variant.total_unit_price, Decimal("1560.00"))

    def test_product_archive(self):
        """Verifies product can be archived, preserving the record."""
        self.product.archive()
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, StatusChoices.ARCHIVED)

    def test_variant_archive(self):
        """Verifies variant can be archived."""
        self.variant.archive()
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.status, StatusChoices.ARCHIVED)


class ProductCatalogAPITests(APITestCase):
    def setUp(self):
        self.product_data = {
            "name": "Cloud Storage",
            "type": "Infrastructure",
            "sales_price": "200.00",
            "cost_price": "80.00",
            "notes": "1TB secure cloud storage"
        }
        self.product = Product.objects.create(
            name="ERP Suite",
            type="Software",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("400.00"),
            notes="Core system"
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            attribute_name="Brand",
            value="Odoo",
            price_adjustment=Decimal("560.00")
        )

    def test_create_product_via_api(self):
        """Verifies staff can create a product."""
        url = reverse('product-list')
        response = self.client.post(url, self.product_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Cloud Storage")
        self.assertEqual(response.data['status'], StatusChoices.ACTIVE)
        self.assertEqual(Decimal(response.data['sales_price']), Decimal("200.00"))
        self.assertEqual(Decimal(response.data['cost_price']), Decimal("80.00"))

    def test_cost_price_hidden_from_customer_view(self):
        """
        SECURITY REQUIREMENT:
        Internal cost prices must NEVER be exposed to customers.
        """
        url = f"{reverse('product-detail', kwargs={'pk': self.product.id})}?view_as=customer"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify cost_price is strictly absent
        self.assertNotIn('cost_price', response.data)
        self.assertIn('sales_price', response.data)
        self.assertEqual(Decimal(response.data['sales_price']), Decimal("1000.00"))

    def test_staff_view_includes_cost_price(self):
        """Staff view includes internal cost price for margin analysis."""
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cost_price', response.data)
        self.assertEqual(Decimal(response.data['cost_price']), Decimal("400.00"))

    def test_archive_product_via_api(self):
        """Verifies POST /api/catalog/products/{id}/archive/ marks product archived."""
        url = reverse('product-archive', kwargs={'pk': self.product.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], StatusChoices.ARCHIVED)

    def test_direct_delete_is_blocked(self):
        """Verifies DELETE method is blocked to prevent breaking historical records."""
        url = reverse('product-detail', kwargs={'pk': self.product.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # Ensure product still exists in database
        self.assertTrue(Product.objects.filter(id=self.product.id).exists())

    def test_create_variant_via_api(self):
        """Verifies creating a variant and calculating total_unit_price."""
        url = reverse('product-variant-list')
        variant_data = {
            "product": str(self.product.id),
            "attribute_name": "Tier",
            "value": "Gold",
            "price_adjustment": "250.00"
        }
        response = self.client.post(url, variant_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['attribute_name'], "Tier")
        self.assertEqual(Decimal(response.data['total_unit_price']), Decimal("1250.00"))

    def test_negative_sales_price_rejected(self):
        """Verifies negative sales prices are rejected by validator."""
        url = reverse('product-list')
        invalid_data = {
            "name": "Invalid Product",
            "sales_price": "-10.00",
            "cost_price": "5.00"
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



from datetime import date, timedelta
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import SubscriptionPlan, BillingInterval, Plan
from .pricing import PricingService, round_money


class SubscriptionPlanModelTests(TestCase):
    def setUp(self):
        self.primary_prod = Product.objects.create(
            name="ERP Core",
            type="Software",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("350.00")
        )
        self.variant = ProductVariant.objects.create(
            product=self.primary_prod,
            attribute_name="Edition",
            value="Enterprise",
            price_adjustment=Decimal("560.00")
        )

    def test_plan_creation_with_defaults(self):
        """Verifies plan creation with PRD defaults."""
        plan = SubscriptionPlan.objects.create(
            name="Starter Monthly",
            billing_interval=BillingInterval.MONTHLY
        )
        self.assertEqual(plan.min_quantity, 1)
        self.assertFalse(plan.allow_pause)
        self.assertFalse(plan.allow_early_closure)
        self.assertTrue(plan.allow_renewal)
        self.assertTrue(plan.auto_close_at_expiry)
        self.assertEqual(plan.status, StatusChoices.ACTIVE)
        self.assertEqual(plan.default_payment_terms, "Immediate")
        self.assertEqual(plan.price, None)
        self.assertEqual(plan.payment_terms, "Immediate")
        # Plan alias check
        self.assertEqual(Plan, SubscriptionPlan)

    def test_all_billing_intervals_supported(self):
        """Verifies daily, weekly, monthly, and yearly billing intervals."""
        intervals = [
            BillingInterval.DAILY,
            BillingInterval.WEEKLY,
            BillingInterval.MONTHLY,
            BillingInterval.YEARLY
        ]
        for interval in intervals:
            p = SubscriptionPlan.objects.create(
                name=f"Plan {interval}",
                billing_interval=interval
            )
            self.assertEqual(p.billing_interval, interval)

    def test_invalid_date_range_rejected(self):
        """Verifies start date cannot be after end date."""
        plan = SubscriptionPlan(
            name="Invalid Promo Plan",
            billing_interval=BillingInterval.YEARLY,
            availability_start_date=date(2026, 12, 31),
            availability_end_date=date(2026, 1, 1)
        )
        with self.assertRaises(DjangoValidationError):
            plan.clean()

    def test_invalid_min_quantity_rejected(self):
        """Verifies minimum quantity < 1 raises ValidationError."""
        plan = SubscriptionPlan(
            name="Invalid Min Qty Plan",
            billing_interval=BillingInterval.MONTHLY,
            min_quantity=0
        )
        with self.assertRaises(DjangoValidationError):
            plan.clean()

    def test_invalid_negative_price_rejected(self):
        """Verifies negative default primary price raises ValidationError."""
        plan = SubscriptionPlan(
            name="Negative Price Plan",
            billing_interval=BillingInterval.MONTHLY,
            default_primary_unit_price=Decimal("-50.00")
        )
        with self.assertRaises(DjangoValidationError):
            plan.clean()

    def test_plan_archive(self):
        """Verifies plan can be archived."""
        plan = SubscriptionPlan.objects.create(
            name="Legacy Plan",
            billing_interval=BillingInterval.DAILY
        )
        plan.archive()
        plan.refresh_from_db()
        self.assertEqual(plan.status, StatusChoices.ARCHIVED)
        self.assertFalse(plan.is_available_on())

    def test_is_available_on_date(self):
        """Verifies dynamic availability window calculation."""
        today = date.today()
        plan = SubscriptionPlan.objects.create(
            name="Seasonal Summer",
            billing_interval=BillingInterval.MONTHLY,
            availability_start_date=today - timedelta(days=5),
            availability_end_date=today + timedelta(days=5)
        )
        self.assertTrue(plan.is_available_on(today))
        self.assertTrue(plan.is_available(today))
        self.assertFalse(plan.is_available_on(today - timedelta(days=10)))
        self.assertFalse(plan.is_available_on(today + timedelta(days=10)))

    def test_property_aliases(self):
        """Verifies price, availability_start, availability_end, payment_terms property aliases."""
        today = date.today()
        plan = SubscriptionPlan(
            name="Alias Test Plan",
            billing_interval=BillingInterval.MONTHLY,
            availability_start_date=today,
            availability_end_date=today + timedelta(days=30),
            default_payment_terms="Net 45",
            default_primary_unit_price=Decimal("499.00")
        )
        self.assertEqual(plan.price, Decimal("499.00"))
        self.assertEqual(plan.payment_terms, "Net 45")
        self.assertEqual(plan.availability_start, today)
        self.assertEqual(plan.availability_end, today + timedelta(days=30))


class SubscriptionPlanPricingInterpretationTests(TestCase):
    """
    Validates Brightloop PRD §7.4 Agreed Pricing Interpretation:
    - Subscription line unit prices are the source of recurring charges.
    - A plan may define a default per-unit price for a designated primary product.
    - That default replaces the primary product's base price before variant adjustments.
    - Add-ons use their own product prices.
    - The plan price is not added again as a separate charge.
    - The quotation displays the resulting prices before confirmation.
    """
    def setUp(self):
        self.primary_prod = Product.objects.create(
            name="ERP Suite",
            type="Software",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("400.00")
        )
        self.variant_odoo = ProductVariant.objects.create(
            product=self.primary_prod,
            attribute_name="Brand",
            value="Odoo",
            price_adjustment=Decimal("560.00")
        )
        self.addon_prod = Product.objects.create(
            name="Cloud Backup",
            type="Storage",
            sales_price=Decimal("200.00"),
            cost_price=Decimal("80.00")
        )
        self.addon_variant = ProductVariant.objects.create(
            product=self.addon_prod,
            attribute_name="Capacity",
            value="5TB",
            price_adjustment=Decimal("50.00")
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Enterprise Monthly",
            billing_interval=BillingInterval.MONTHLY,
            min_quantity=5,
            primary_product=self.primary_prod,
            default_primary_unit_price=Decimal("800.00"),
            allow_pause=True,
            allow_renewal=True,
            default_payment_terms="Net 30"
        )

    def test_prd_agreed_pricing_primary_product_override(self):
        """
        PRD §7.4 Rule:
        Plan default price (800) replaces primary product base price (1,000)
        before variant adjustments (560). Resulting unit price = 800 + 560 = 1,360.
        """
        unit_price = self.plan.calculate_unit_price(
            product=self.primary_prod,
            variant=self.variant_odoo
        )
        self.assertEqual(unit_price, Decimal("1360.00"))

    def test_addon_products_use_own_catalog_prices(self):
        """
        PRD §7.4 Rule:
        Add-ons use their own product prices (not overridden by plan price).
        Cloud Backup: base 200 + 5TB variant 50 = 250.00.
        """
        addon_unit_price = self.plan.calculate_unit_price(
            product=self.addon_prod,
            variant=self.addon_variant
        )
        self.assertEqual(addon_unit_price, Decimal("250.00"))

    def test_no_separate_plan_charge_and_total_calculation(self):
        """
        PRD §7.4 Rule:
        Plan price is NOT added as a separate charge.
        Total = (5 × 1,360.00) + (2 × 250.00) = 6,800.00 + 500.00 = 7,300.00.
        """
        lines = [
            {
                "product": self.primary_prod,
                "variant": self.variant_odoo,
                "quantity": 5
            },
            {
                "product": self.addon_prod,
                "variant": self.addon_variant,
                "quantity": 2
            }
        ]
        breakdown = PricingService.calculate_plan_quote(self.plan, lines)

        self.assertEqual(breakdown['recurring_subtotal'], Decimal("7300.00"))
        self.assertTrue(breakdown['min_quantity_met'])
        self.assertEqual(breakdown['pricing_policy']['separate_plan_charge'], Decimal('0.00'))
        self.assertEqual(len(breakdown['lines']), 2)
        # Line 1: Primary product
        self.assertTrue(breakdown['lines'][0]['is_primary'])
        self.assertEqual(breakdown['lines'][0]['base_price_source'], 'plan_override')
        self.assertEqual(breakdown['lines'][0]['unit_price'], Decimal("1360.00"))
        self.assertEqual(breakdown['lines'][0]['line_subtotal'], Decimal("6800.00"))
        # Line 2: Add-on product
        self.assertFalse(breakdown['lines'][1]['is_primary'])
        self.assertEqual(breakdown['lines'][1]['base_price_source'], 'product_catalog')
        self.assertEqual(breakdown['lines'][1]['unit_price'], Decimal("250.00"))
        self.assertEqual(breakdown['lines'][1]['line_subtotal'], Decimal("500.00"))

    def test_minimum_quantity_enforcement(self):
        """Verifies warning when primary quantity is below plan min_quantity."""
        lines = [
            {
                "product": self.primary_prod,
                "variant": self.variant_odoo,
                "quantity": 2  # Less than plan.min_quantity = 5
            }
        ]
        breakdown = PricingService.calculate_plan_quote(self.plan, lines, validate_minimums=True)
        self.assertFalse(breakdown['min_quantity_met'])
        self.assertIn("below the required plan minimum", breakdown['min_quantity_error'])

    def test_unavailable_plan_cannot_be_quoted(self):
        """Archived or date-ineligible plans cannot be quoted."""
        self.plan.archive()
        lines = [{"product": self.primary_prod, "quantity": 5}]
        with self.assertRaises(DRFValidationError):
            PricingService.calculate_plan_quote(self.plan, lines)


class SubscriptionPlanAPITests(APITestCase):
    def setUp(self):
        self.primary_prod = Product.objects.create(
            name="ERP Suite",
            type="Software",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("400.00")
        )
        self.variant_odoo = ProductVariant.objects.create(
            product=self.primary_prod,
            attribute_name="Brand",
            value="Odoo",
            price_adjustment=Decimal("560.00")
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Enterprise Annual",
            billing_interval=BillingInterval.YEARLY,
            min_quantity=5,
            primary_product=self.primary_prod,
            default_primary_unit_price=Decimal("800.00"),
            allow_pause=True,
            default_payment_terms="Net 30"
        )

    def test_create_plan_via_api(self):
        """Verifies creating a plan with full policy configuration."""
        url = reverse('subscription-plan-list')
        payload = {
            "name": "Team Weekly",
            "billing_interval": "weekly",
            "min_quantity": 2,
            "allow_pause": False,
            "allow_early_closure": True,
            "allow_renewal": True,
            "auto_close_at_expiry": True,
            "default_payment_terms": "Net 15",
            "primary_product": str(self.primary_prod.id),
            "default_primary_unit_price": "750.00"
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Team Weekly")
        self.assertEqual(response.data['billing_interval'], "weekly")
        self.assertEqual(response.data['min_quantity'], 2)
        self.assertTrue(response.data['allow_early_closure'])
        self.assertEqual(Decimal(response.data['default_primary_unit_price']), Decimal("750.00"))
        self.assertEqual(response.data['primary_product_name'], "ERP Suite")

    def test_filter_plans_by_billing_interval(self):
        """Verifies filtering plans by billing interval."""
        SubscriptionPlan.objects.create(
            name="Quick Daily",
            billing_interval=BillingInterval.DAILY
        )
        url = f"{reverse('subscription-plan-list')}?billing_interval=yearly"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Enterprise Annual")

    def test_archive_plan_via_api(self):
        """Verifies POST /api/catalog/plans/{id}/archive/ marks plan archived."""
        url = reverse('subscription-plan-archive', kwargs={'pk': self.plan.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], StatusChoices.ARCHIVED)

    def test_direct_plan_delete_blocked(self):
        """Verifies hard DELETE is blocked to protect historical subscriptions."""
        url = reverse('subscription-plan-detail', kwargs={'pk': self.plan.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(SubscriptionPlan.objects.filter(id=self.plan.id).exists())

    def test_customer_view_filters_active_and_available_plans(self):
        """Customer view only returns active and currently available plans."""
        today = date.today()
        # Create an expired plan
        SubscriptionPlan.objects.create(
            name="Past Promo",
            billing_interval=BillingInterval.MONTHLY,
            availability_start_date=today - timedelta(days=30),
            availability_end_date=today - timedelta(days=10),
            status=StatusChoices.ACTIVE
        )
        # Create an archived plan
        SubscriptionPlan.objects.create(
            name="Archived Plan",
            billing_interval=BillingInterval.MONTHLY,
            status=StatusChoices.ARCHIVED
        )
        url = f"{reverse('subscription-plan-list')}?view_as=customer"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        plan_names = [p['name'] for p in response.data]
        self.assertIn("Enterprise Annual", plan_names)
        self.assertNotIn("Past Promo", plan_names)
        self.assertNotIn("Archived Plan", plan_names)

    def test_pricing_calculation_endpoint(self):
        """
        Verifies POST /api/catalog/plans/{id}/calculate_pricing/ calculates
        accurate prices under PRD §7.4 rules.
        """
        url = reverse('subscription-plan-calculate-pricing', kwargs={'pk': self.plan.id})
        payload = {
            "lines": [
                {
                    "product_id": str(self.primary_prod.id),
                    "variant_id": str(self.variant_odoo.id),
                    "quantity": 10
                }
            ]
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 800 (plan override) + 560 (variant) = 1,360.00 unit price * 10 = 13,600.00
        self.assertEqual(Decimal(str(response.data['recurring_subtotal'])), Decimal("13600.00"))
        self.assertTrue(response.data['min_quantity_met'])
        self.assertEqual(len(response.data['lines']), 1)
        self.assertEqual(Decimal(str(response.data['lines'][0]['unit_price'])), Decimal("1360.00"))
        self.assertTrue(response.data['lines'][0]['is_primary'])

    def test_alias_endpoint_subscription_plans(self):
        """Verifies /api/catalog/subscription-plans/ alias router endpoint."""
        url = reverse('subscription-plan-alias-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)


class PricingMathematicalInvariantsTests(TestCase):
    """
    Mathematical invariant tests enforcing PRD §7.4 and TECK_STACK.md monetary rules:
    - Decimal arithmetic with ROUND_HALF_UP precision.
    - Zero separate plan charge invariant.
    - Price non-negativity under extreme negative variant adjustments.
    - Add-on price invariance under plan primary product price alterations.
    """
    def setUp(self):
        self.primary = Product.objects.create(
            name="Platform Base",
            sales_price=Decimal("500.00"),
            cost_price=Decimal("100.00")
        )
        self.addon = Product.objects.create(
            name="Extra Bandwidth",
            sales_price=Decimal("120.00"),
            cost_price=Decimal("40.00")
        )

    def test_non_negativity_under_heavy_negative_adjustment(self):
        """Ensures unit price cannot become negative even if variant has extreme discount."""
        heavy_negative_variant = ProductVariant.objects.create(
            product=self.primary,
            attribute_name="Discount",
            value="Special Promo",
            price_adjustment=Decimal("-9999.00")
        )
        plan = SubscriptionPlan.objects.create(
            name="Discounted Monthly",
            billing_interval=BillingInterval.MONTHLY,
            primary_product=self.primary,
            default_primary_unit_price=Decimal("100.00")
        )
        unit_price = plan.calculate_unit_price(self.primary, heavy_negative_variant)
        self.assertEqual(unit_price, Decimal("0.00"))

    def test_addon_price_independence_invariant(self):
        """Varying plan price never changes add-on product prices."""
        plan1 = SubscriptionPlan.objects.create(
            name="Plan 1",
            billing_interval=BillingInterval.MONTHLY,
            primary_product=self.primary,
            default_primary_unit_price=Decimal("200.00")
        )
        plan2 = SubscriptionPlan.objects.create(
            name="Plan 2",
            billing_interval=BillingInterval.MONTHLY,
            primary_product=self.primary,
            default_primary_unit_price=Decimal("900.00")
        )
        price_under_plan1 = plan1.calculate_unit_price(self.addon)
        price_under_plan2 = plan2.calculate_unit_price(self.addon)
        self.assertEqual(price_under_plan1, self.addon.sales_price)
        self.assertEqual(price_under_plan2, self.addon.sales_price)
        self.assertEqual(price_under_plan1, price_under_plan2)

    def test_total_equals_sum_of_lines_exactly(self):
        """Asserts total recurring charge is strictly sum of rounded line subtotals."""
        plan = SubscriptionPlan.objects.create(
            name="Scale Plan",
            billing_interval=BillingInterval.MONTHLY,
            primary_product=self.primary,
            default_primary_unit_price=Decimal("450.55")
        )
        lines = [
            {"product": self.primary, "quantity": 3},
            {"product": self.addon, "quantity": 7}
        ]
        breakdown = PricingService.calculate_plan_quote(plan, lines)
        calculated_subtotal = breakdown['recurring_subtotal']
        expected_subtotal = round_money(
            round_money(Decimal("450.55") * 3) + round_money(Decimal("120.00") * 7)
        )
        self.assertEqual(calculated_subtotal, expected_subtotal)


