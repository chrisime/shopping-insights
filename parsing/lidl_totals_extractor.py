"""Extract Lidl totals from preprocessed receipt aggregates."""

from __future__ import annotations

from typing import Optional

from .receipt_totals import ReceiptTotalsExtractionResult


def extract_lidl_totals(
    total_no_saving: float,
    amount_saved: Optional[float] = None,
    lidlplus_amount_saved: Optional[float] = None,
    sticker_discount_amount: Optional[float] = None,
    saved_deposit: float = 0.0,
) -> ReceiptTotalsExtractionResult:
    """Calculate Lidl totals from already normalized aggregate inputs."""
    regular_saved_amount = _round_optional(amount_saved)
    lidlplus_saved_amount = _round_optional(lidlplus_amount_saved)
    sticker_saved_amount = _round_optional(sticker_discount_amount)
    saved_deposit = round(saved_deposit, 2) if saved_deposit > 0 else None

    total_savings = sum(
        value
        for value in (
            regular_saved_amount,
            lidlplus_saved_amount,
            sticker_saved_amount,
            saved_deposit,
        )
        if value is not None
    )

    total_price_no_saving = round(total_no_saving, 2) if total_no_saving > 0 else None

    total_price = None
    if total_no_saving > 0:
        final_paid = total_no_saving - total_savings
        if final_paid > 0:
            total_price = round(final_paid, 2)

    additional_savings = {}
    if lidlplus_saved_amount:
        additional_savings["lidlplus_amount_saved"] = lidlplus_saved_amount
    if sticker_saved_amount:
        additional_savings["sticker_discount_amount"] = sticker_saved_amount

    return ReceiptTotalsExtractionResult(
        total_price_no_saving=total_price_no_saving,
        amount_saved=regular_saved_amount,
        saved_deposit=saved_deposit,
        total_price=total_price,
        total_savings=round(total_savings, 2),
        additional_savings=additional_savings,
    )


def _round_optional(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), 2)
