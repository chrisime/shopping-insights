"""Extract REWE totals from parsed receipt aggregates."""

from __future__ import annotations

from typing import Optional

from .rewe_parser_common import to_rewe_float
from .receipt_totals import ReceiptTotalsExtractionResult


def extract_rewe_totals(
    raw_total_price: Optional[float],
    total_no_saving: float,
    saved_amount: float,
    saved_pfand: float,
    rewe_bonus_saved_amount: float,
) -> ReceiptTotalsExtractionResult:
    """Calculate schema-ready REWE totals from parsed raw sums."""
    total_price_float: Optional[float] = None
    if raw_total_price is not None:
        total_price_float = to_rewe_float(raw_total_price)
    elif total_no_saving > 0:
        total_price_float = total_no_saving - saved_amount - saved_pfand

    if total_price_float is not None:
        total_price_float = max(total_price_float - rewe_bonus_saved_amount, 0.0)

    additional_savings = {}
    if rewe_bonus_saved_amount >= 0:
        additional_savings["rewe_bonus_amount_saved"] = round(rewe_bonus_saved_amount, 2)

    total_savings = saved_amount + saved_pfand + rewe_bonus_saved_amount

    return ReceiptTotalsExtractionResult(
        total_price_no_saving=round(total_no_saving, 2) if total_no_saving > 0 else None,
        amount_saved=round(saved_amount, 2) if saved_amount > 0 else None,
        saved_deposit=round(saved_pfand, 2) if saved_pfand > 0 else None,
        total_price=round(total_price_float, 2) if total_price_float is not None else None,
        total_savings=round(total_savings, 2),
        additional_savings=additional_savings,
    )

