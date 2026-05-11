"""Extract Lidl totals from preprocessed receipt aggregates."""

from __future__ import annotations

from typing import Any, Optional

from bs4 import BeautifulSoup

from .lidl_totals_preprocessor import extract_lidl_totals_input
from .receipt_totals_result import ReceiptTotalsResult


def extract_lidl_totals(
    soup: BeautifulSoup,
    amount_saved: Optional[Any] = None,
    lidlplus_amount_saved: Optional[Any] = None,
    sticker_discount_amount: Optional[Any] = None,
) -> ReceiptTotalsResult:
    """Calculate Lidl totals directly from receipt soup and optional savings fields."""
    totals_input = extract_lidl_totals_input(
        soup,
        amount_saved=amount_saved,
        lidlplus_amount_saved=lidlplus_amount_saved,
        sticker_discount_amount=sticker_discount_amount,
    )
    return _calculate_lidl_totals(
        amount_saved=totals_input.amount_saved,
        lidlplus_amount_saved=totals_input.lidlplus_amount_saved,
        sticker_discount_amount=totals_input.sticker_discount_amount,
        saved_deposit=totals_input.saved_deposit,
    )


def _calculate_lidl_totals(
    amount_saved: Optional[float] = None,
    lidlplus_amount_saved: Optional[float] = None,
    sticker_discount_amount: Optional[float] = None,
    saved_deposit: float = 0.0,
) -> ReceiptTotalsResult:
    """Calculate Lidl totals from already normalized aggregate inputs."""
    regular_saved_amount = _round_optional(amount_saved)
    lidlplus_saved_amount = _round_optional(lidlplus_amount_saved)
    sticker_saved_amount = _round_optional(sticker_discount_amount)
    saved_deposit = round(saved_deposit, 2) if saved_deposit > 0 else None

    additional_savings = {}
    if lidlplus_saved_amount:
        additional_savings["lidlplus_amount_saved"] = lidlplus_saved_amount
    if sticker_saved_amount:
        additional_savings["sticker_discount_amount"] = sticker_saved_amount

    return ReceiptTotalsResult(
        amount_saved=regular_saved_amount,
        saved_deposit=saved_deposit,
        total_price=None,
        additional_savings=additional_savings,
    )


def _round_optional(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 2)
