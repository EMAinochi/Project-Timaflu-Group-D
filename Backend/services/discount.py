"""Order discount calculation (verkoopproces — productbeschrijving punt 1)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

ORDER_DISCOUNT_THRESHOLD = Decimal("500")
ORDER_DISCOUNT_RATE = Decimal("0.05")
FIRST_ORDER_DISCOUNT_RATE = Decimal("0.10")


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def discount_pct_from_turnover(turnover: Decimal) -> Decimal:
    """Tabel 1 — jaaromzet bepaalt klantkorting."""
    if turnover >= Decimal("20000"):
        return Decimal("0.15")
    if turnover >= Decimal("10000"):
        return Decimal("0.10")
    return Decimal("0.05")


@dataclass
class DiscountResult:
    subtotal: Decimal
    order_discount: Decimal
    first_order_discount: Decimal
    customer_discount: Decimal
    total: Decimal
    order_discount_pct: Decimal
    customer_discount_pct: Decimal
    is_first_order: bool


def calculate_order_discounts(
    subtotal: float | Decimal,
    *,
    is_first_order: bool,
    has_one_time_discount: bool,
    customer_discount_pct: float | Decimal | None = None,
    annual_turnover: float | Decimal | None = None,
) -> DiscountResult:
    """
    Productbeschrijving — Berekenen korting bestelling (verkoop):

    1. Invoer: subtotaal (optelsom bestelde producten)
    2. Bestellingskorting: 5% bij subtotaal >= € 500, van subtotaal af
    3. Eerste bestelling (of eenmalige acquisitie-korting): 10% van restbedrag af
    4. Klantenkorting: percentage uit Tabel 1 op basis van jaaromzet (aangekochte
       producten afgelopen kalenderjaar), van restbedrag af
    5. Uitkomst: totaalbedrag na alle kortingen
    """
    amount = _money(Decimal(str(subtotal)))
    order_discount = Decimal("0")
    order_discount_pct = Decimal("0")

    if amount >= ORDER_DISCOUNT_THRESHOLD:
        order_discount_pct = ORDER_DISCOUNT_RATE
        order_discount = _money(amount * ORDER_DISCOUNT_RATE)
    after_order = amount - order_discount

    apply_first = is_first_order or has_one_time_discount
    first_order_discount = (
        _money(after_order * FIRST_ORDER_DISCOUNT_RATE) if apply_first else Decimal("0")
    )
    after_first = after_order - first_order_discount

    if customer_discount_pct is not None:
        pct = Decimal(str(customer_discount_pct)) / Decimal("100")
    elif annual_turnover is not None:
        pct = discount_pct_from_turnover(Decimal(str(annual_turnover)))
    else:
        pct = Decimal("0.05")

    customer_discount = _money(after_first * pct)
    total = _money(after_first - customer_discount)

    return DiscountResult(
        subtotal=amount,
        order_discount=order_discount,
        first_order_discount=first_order_discount,
        customer_discount=customer_discount,
        total=total,
        order_discount_pct=order_discount_pct,
        customer_discount_pct=pct,
        is_first_order=apply_first,
    )
