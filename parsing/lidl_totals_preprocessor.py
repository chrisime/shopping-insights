"""Preprocess Lidl totals inputs before final totals aggregation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class LidlTotalsInput:
    """Normalized Lidl totals inputs prepared before final aggregation."""

    total_no_saving: float
    amount_saved: Optional[float]
    lidlplus_amount_saved: Optional[float]
    sticker_discount_amount: Optional[float]
    saved_deposit: float



def extract_lidl_totals_input(
    soup: BeautifulSoup,
    items: List[Dict[str, Any]],
    amount_saved: Optional[Any] = None,
    lidlplus_amount_saved: Optional[Any] = None,
    sticker_discount_amount: Optional[Any] = None,
) -> LidlTotalsInput:
    """Prepare all Lidl totals inputs before they are passed to the totals extractor."""
    return LidlTotalsInput(
        total_no_saving=_sum_item_totals(items),
        amount_saved=_coerce_optional_float(amount_saved),
        lidlplus_amount_saved=_coerce_optional_float(lidlplus_amount_saved),
        sticker_discount_amount=_coerce_optional_float(sticker_discount_amount),
        saved_deposit=_extract_pfand_savings_from_html(soup),
    )



def _sum_item_totals(items: List[Dict[str, Any]]) -> float:
    total_from_items = 0.0
    for item in items or []:
        try:
            item_price = float(item.get("price", 0) or 0)
            item_qty = float(item.get("quantity", 1) or 1)
            total_from_items += item_price * item_qty
        except (ValueError, TypeError, AttributeError):
            continue
    return total_from_items



def _coerce_optional_float(value: Optional[Any]) -> Optional[float]:
    if not value:
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

