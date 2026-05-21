"""Extract and calculate Lidl totals from receipt HTML and parsed discount fields."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ReceiptTotalsDTO:
    """Common totals result used by Lidl and REWE extractors."""

    discount: Optional[float]
    saved_deposit: Optional[float]
    total_price: Optional[float]
    additional_savings: Dict[str, float] = field(default_factory=dict)


def extract_lidl_totals(
    soup: BeautifulSoup,
    discount: Optional[Any] = None,
    lidlplus_discount: Optional[Any] = None,
    sticker_discount: Optional[Any] = None,
) -> ReceiptTotalsDTO:
    """Extract and calculate Lidl totals in one step from HTML + parsed fields."""
    coerced_discount = _round_optional(_coerce_optional_float(discount))
    coerced_lidlplus = _round_optional(_coerce_optional_float(lidlplus_discount))
    coerced_sticker = _round_optional(_coerce_optional_float(sticker_discount))
    saved_deposit = _extract_pfand_savings_from_html(soup)
    rounded_deposit = round(saved_deposit, 2) if saved_deposit > 0 else None

    additional_savings: Dict[str, float] = {}
    if coerced_lidlplus:
        additional_savings["lidlplus_discount"] = coerced_lidlplus
    if coerced_sticker:
        additional_savings["sticker_discount"] = coerced_sticker

    return ReceiptTotalsDTO(
        discount=coerced_discount,
        saved_deposit=rounded_deposit,
        total_price=None,
        additional_savings=additional_savings,
    )


def _coerce_optional_float(value: Optional[Any]) -> Optional[float]:
    if not value:
        return None
    try:
        return round(float(value), 2)
    except (ValueError, TypeError, AttributeError):
        return None


def _round_optional(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 2)


def _extract_pfand_savings_from_html(soup: BeautifulSoup) -> float:
    purchase_list = soup.find("span", class_="purchase_list")
    if not purchase_list:
        return 0.0

    purchase_text = purchase_list.get_text()
    pfand_savings = 0.0

    pfand_matches = re.findall(r"Pfandrückgabe\s*(-?\d+,\d+)", purchase_text)
    for match in pfand_matches:
        try:
            pfand_savings += abs(float(match.replace(",", ".")))
        except (ValueError, AttributeError):
            continue

    if pfand_savings > 0:
        return pfand_savings

    pfand_calc_matches = re.findall(r"(-?\d+)\s*x\s*(-?\d+,\d+)", purchase_text)
    for qty_match, price_match in pfand_calc_matches:
        try:
            qty = float(qty_match)
            price = float(price_match.replace(",", "."))
            pfand_savings += abs(qty * price)
        except (ValueError, AttributeError):
            continue

    return pfand_savings
