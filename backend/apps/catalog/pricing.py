from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from datetime import date
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import Product, ProductVariant, SubscriptionPlan, StatusChoices

MONEY_PRECISION = Decimal('0.01')


def round_money(amount: Decimal | float | str | int) -> Decimal:
    """
    Rounds monetary amounts using ROUND_HALF_UP to 2 decimal places
    per Brightloop PRD §8 and TECK_STACK.md §4.
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return amount.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


class PricingService:
    """
    Implements the agreed pricing interpretation from Brightloop PRD §7.4:
    - Subscription line unit prices are the source of recurring charges.
    - A plan may define a default per-unit price for a designated primary product.
    - That default replaces the primary product's base price before variant adjustments.
    - Add-ons use their own product prices.
    - The plan price is not added again as a separate charge.
    - The quotation displays the resulting prices before confirmation.
    """

    @staticmethod
    def calculate_line_unit_price(
        plan: Optional[SubscriptionPlan],
        product: Product,
        variant: Optional[ProductVariant] = None,
        is_primary: Optional[bool] = None
    ) -> Decimal:
        """
        Calculates the effective per-unit price for a product line within a plan.
        """
        # Determine whether this product is the primary product
        if is_primary is not None:
            treated_as_primary = is_primary
        elif plan and plan.primary_product_id:
            treated_as_primary = (plan.primary_product_id == product.id)
        else:
            treated_as_primary = False

        # Apply PRD §7.4: Plan default price overrides primary product's base price
        if treated_as_primary and plan and plan.default_primary_unit_price is not None:
            base_price = Decimal(str(plan.default_primary_unit_price))
        else:
            base_price = Decimal(str(product.sales_price))

        # Add variant price adjustment (if present)
        variant_adj = Decimal('0.00')
        if variant:
            variant_adj = Decimal(str(variant.price_adjustment))

        effective_unit_price = base_price + variant_adj

        # Ensure unit price is non-negative
        if effective_unit_price < Decimal('0.00'):
            effective_unit_price = Decimal('0.00')

        return round_money(effective_unit_price)

    @classmethod
    def calculate_plan_quote(
        cls,
        plan: SubscriptionPlan,
        lines: List[Dict[str, Any]],
        quote_date: Optional[date] = None,
        validate_minimums: bool = True
    ) -> Dict[str, Any]:
        """
        Computes the complete commercial pricing breakdown for a quote or subscription under a plan.
        Input format for lines:
        [
            {
                "product": Product or "product_id": uuid,
                "variant": Optional[ProductVariant] or "variant_id": Optional[uuid],
                "quantity": int,
                "is_primary": Optional[bool]
            }
        ]
        """
        if quote_date is None:
            quote_date = timezone.now().date()

        # Validate plan availability
        if not plan.is_available_on(quote_date):
            raise ValidationError(
                f"Plan '{plan.name}' is not currently available for quotations on {quote_date}."
            )

        calculated_lines = []
        total_primary_quantity = 0

        for idx, line_data in enumerate(lines):
            # Resolve product
            product = line_data.get('product')
            if not product and 'product_id' in line_data:
                try:
                    product = Product.objects.get(id=line_data['product_id'])
                except Product.DoesNotExist:
                    raise ValidationError(f"Product with id {line_data['product_id']} does not exist.")

            if not product:
                raise ValidationError(f"Line {idx + 1} is missing a valid product.")

            # Resolve variant
            variant = line_data.get('variant')
            if not variant and line_data.get('variant_id'):
                try:
                    variant = ProductVariant.objects.get(id=line_data['variant_id'], product=product)
                except ProductVariant.DoesNotExist:
                    raise ValidationError(
                        f"Variant with id {line_data['variant_id']} not found for product {product.name}."
                    )

            # Resolve quantity
            quantity = int(line_data.get('quantity', 1))
            if quantity < 1:
                raise ValidationError(f"Quantity for product '{product.name}' must be at least 1.")

            # Determine primary flag
            explicit_is_primary = line_data.get('is_primary')
            if explicit_is_primary is not None:
                is_primary = bool(explicit_is_primary)
            elif plan.primary_product_id:
                is_primary = (plan.primary_product_id == product.id)
            else:
                # If plan has no primary product specified but has a default price and this is the first line:
                is_primary = (idx == 0 and plan.default_primary_unit_price is not None)

            if is_primary:
                total_primary_quantity += quantity

            # Determine base price and source
            if is_primary and plan.default_primary_unit_price is not None:
                base_price = round_money(plan.default_primary_unit_price)
                base_price_source = 'plan_override'
            else:
                base_price = round_money(product.sales_price)
                base_price_source = 'product_catalog'

            variant_adj = round_money(variant.price_adjustment) if variant else Decimal('0.00')
            unit_price = cls.calculate_line_unit_price(
                plan=plan,
                product=product,
                variant=variant,
                is_primary=is_primary
            )
            line_subtotal = round_money(unit_price * quantity)

            calculated_lines.append({
                'line_number': idx + 1,
                'product_id': str(product.id),
                'product_name': product.name,
                'product_type': product.type,
                'variant_id': str(variant.id) if variant else None,
                'variant_name': f"{variant.attribute_name}: {variant.value}" if variant else None,
                'is_primary': is_primary,
                'base_price': base_price,
                'base_price_source': base_price_source,
                'variant_adjustment': variant_adj,
                'unit_price': unit_price,
                'quantity': quantity,
                'line_subtotal': line_subtotal
            })

        # Minimum quantity validation
        min_quantity_met = True
        min_quantity_error = None
        if validate_minimums:
            # PRD: minimum quantity applies to plan activation
            relevant_quantity = total_primary_quantity if total_primary_quantity > 0 else sum(l['quantity'] for l in calculated_lines)
            if relevant_quantity < plan.min_quantity:
                min_quantity_met = False
                min_quantity_error = (
                    f"Selected quantity ({relevant_quantity}) is below the required plan minimum quantity of {plan.min_quantity}."
                )

        recurring_subtotal = round_money(sum(line['line_subtotal'] for line in calculated_lines))

        return {
            'plan_id': str(plan.id),
            'plan_name': plan.name,
            'billing_interval': plan.billing_interval,
            'default_payment_terms': plan.default_payment_terms,
            'quote_date': str(quote_date),
            'min_quantity_required': plan.min_quantity,
            'min_quantity_met': min_quantity_met,
            'min_quantity_error': min_quantity_error,
            'lines': calculated_lines,
            'recurring_subtotal': recurring_subtotal,
            'pricing_policy': {
                'rule': 'PRD §7.4: Subscription line unit prices are the source of recurring charges. Plan price is not added as a separate charge.',
                'plan_price_applied': plan.default_primary_unit_price is not None,
                'separate_plan_charge': Decimal('0.00')
            }
        }
