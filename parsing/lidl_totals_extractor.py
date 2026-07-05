"""Extract and calculate Lidl totals from receipt HTML and parsed discount fields."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, Optional

from shared.float_parser import parse_german_float
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
    coerced_discount = _coerce_optional_float(discount)
    coerced_lidlplus = _coerce_optional_float(lidlplus_discount)
    coerced_sticker = _coerce_optional_float(sticker_discount)
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
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (ValueError, TypeError, AttributeError):
        return None



def _extract_pfand_savings_from_html(soup: BeautifulSoup) -> float:
    purchase_list = soup.find("span", class_="purchase_list")
    if not purchase_list:
        return 0.0

    purchase_text = purchase_list.get_text()
    pfand_savings = 0.0

    pfand_matches = re.findall(r"Pfandrückgabe\s*(-?\d+,\d+)", purchase_text)
    for match in pfand_matches:
        pfand_savings += abs(parse_german_float(match) or 0.0)

    if pfand_savings > 0:
        return pfand_savings

    pfand_calc_matches = re.findall(r"(-?\d+)\s*x\s*(-?\d+,\d+)", purchase_text)
    for qty_match, price_match in pfand_calc_matches:
        qty = float(qty_match)
        pfand_savings += abs(qty * (parse_german_float(price_match) or 0.0))

    return pfand_savings
