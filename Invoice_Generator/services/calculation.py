"""Feature 1 & PRD 7.9, 8: Monetary rounding and invoice total calculations.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional


CENTS = Decimal("0.01")


def quantize_money(amount: Decimal) -> Decimal:
    """Rounds to 2 decimal places using standard financial round-half-up."""
    return Decimal(str(amount)).quantize(CENTS, rounding=ROUND_HALF_UP)


@dataclass
class InputLine:
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.00")
    tax_rate: Decimal = Decimal("0.00")  # Percentage e.g. 18.00 for 18%


@dataclass
class CalculatedLine:
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    line_total: Decimal


@dataclass
class CalculationResult:
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    lines: List[CalculatedLine]


def calculate(
    lines: List[InputLine],
    discount: Optional[dict] = None
) -> CalculationResult:
    """Calculate invoice item subtotals, tax, discounts, and total.
    
    Supports line discounts or overall subscription discount (fixed or percentage).
    All monetary math uses Decimal with ROUND_HALF_UP rounding.
    """
    total_gross = Decimal("0.00")
    prepared_lines = []

    for l in lines:
        qty = Decimal(str(l.quantity))
        price = Decimal(str(l.unit_price))
        gross = quantize_money(qty * price)
        disc = quantize_money(Decimal(str(l.discount_amount or 0)))
        total_gross += gross
        prepared_lines.append({
            "line": l,
            "quantity": qty,
            "unit_price": price,
            "gross": gross,
            "discount": disc,
        })

    # If subscription-level discount is provided, distribute or calculate it
    sub_discount_total = Decimal("0.00")
    if discount and total_gross > Decimal("0.00"):
        disc_type = discount.get("type", "fixed")  # "fixed" or "percentage"
        disc_val = Decimal(str(discount.get("value", 0)))
        if disc_type == "percentage":
            sub_discount_total = quantize_money(total_gross * (disc_val / Decimal("100")))
        else:
            sub_discount_total = quantize_money(disc_val)

        # Cap discount at total_gross
        sub_discount_total = min(sub_discount_total, total_gross)

        # Distribute proportionally across lines
        allocated_so_far = Decimal("0.00")
        num_lines = len(prepared_lines)
        for i, item in enumerate(prepared_lines):
            if i == num_lines - 1:
                # Assign remainder to last line to prevent rounding drift
                line_dist_disc = sub_discount_total - allocated_so_far
            else:
                line_dist_disc = quantize_money(sub_discount_total * (item["gross"] / total_gross))
                allocated_so_far += line_dist_disc
            item["discount"] = quantize_money(item["discount"] + line_dist_disc)

    calc_lines: List[CalculatedLine] = []
    agg_subtotal = Decimal("0.00")
    agg_discount = Decimal("0.00")
    agg_tax = Decimal("0.00")
    agg_total = Decimal("0.00")

    for item in prepared_lines:
        line_obj = item["line"]
        qty = item["quantity"]
        unit_price = item["unit_price"]
        gross = item["gross"]
        disc = min(item["discount"], gross)
        taxable_amount = gross - disc

        tax_rate = Decimal(str(line_obj.tax_rate or 0))
        tax_amount = quantize_money(taxable_amount * (tax_rate / Decimal("100")))
        line_total = quantize_money(taxable_amount + tax_amount)

        agg_subtotal += gross
        agg_discount += disc
        agg_tax += tax_amount
        agg_total += line_total

        calc_lines.append(
            CalculatedLine(
                description=line_obj.description,
                quantity=qty,
                unit_price=unit_price,
                discount_amount=disc,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                line_total=line_total,
            )
        )

    return CalculationResult(
        subtotal=quantize_money(agg_subtotal),
        discount_total=quantize_money(agg_discount),
        tax_total=quantize_money(agg_tax),
        total=quantize_money(agg_total),
        lines=calc_lines,
    )

