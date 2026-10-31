from decimal import Decimal
import pytest
from billing.services.calculation import calculate, InputLine

def test_single_line_calculation():
    lines = [
        InputLine(
            description="Pro Plan",
            quantity=Decimal("1"),
            unit_price=Decimal("1000.00"),
            discount_amount=Decimal("100.00"),
            tax_rate=Decimal("18.00"),
        )
    ]
    res = calculate(lines)
    assert res.subtotal == Decimal("1000.00")
    assert res.discount_total == Decimal("100.00")
    # Taxable amount = 900.00; 18% of 900 = 162.00
    assert res.tax_total == Decimal("162.00")
    assert res.total == Decimal("1062.00")

def test_prd_illustrative_example():
    # From PRD 8:
    # 10 seats x 500 = 5000, 10% discount = -500 -> Taxable 4500 -> 10% tax = 450 -> Total = 4950
    lines = [
        InputLine(
            description="10 seats",
            quantity=Decimal("10"),
            unit_price=Decimal("500.00"),
            tax_rate=Decimal("10.00"),
        )
    ]
    res = calculate(lines, discount={"type": "percentage", "value": 10})
    assert res.subtotal == Decimal("5000.00")
    assert res.discount_total == Decimal("500.00")
    assert res.tax_total == Decimal("450.00")
    assert res.total == Decimal("4950.00")

