"""Extract REWE totals from parsed receipt aggregates."""

from __future__ import annotations

from typing import Optional

from .rewe_parser_common import to_rewe_float
from .receipt_totals_result import ReceiptTotalsResult


def extract_rewe_totals(
    raw_total_price: Optional[float],
    saved_amount: float,
    saved_deposit: float,
    rewe_bonus_saved_amount: float,
) -> ReceiptTotalsResult:
    """Calculate schema-ready REWE totals from parsed raw sums."""
    total_price_float: Optional[float] = None
    if raw_total_price is not None:
        total_price_float = to_rewe_float(raw_total_price)

    if total_price_float is not None:
        total_price_float = max(total_price_float - rewe_bonus_saved_amount, 0.0)

    additional_savings = {}
    if rewe_bonus_saved_amount >= 0:
        additional_savings["rewe_bonus_amount_saved"] = round(rewe_bonus_saved_amount, 2)

    return ReceiptTotalsResult(
        amount_saved=round(saved_amount, 2) if saved_amount > 0 else None,
        saved_deposit=round(saved_deposit, 2) if saved_deposit > 0 else None,
        total_price=round(total_price_float, 2) if total_price_float is not None else None,
        additional_savings=additional_savings,
    )

