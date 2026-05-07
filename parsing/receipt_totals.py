"""Shared totals result types for receipt parsers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class ReceiptTotalsExtractionResult:
    """Common totals result used by Lidl and REWE extractors."""

    total_price_no_saving: Optional[float]
    amount_saved: Optional[float]
    saved_deposit: Optional[float]
    total_price: Optional[float]
    total_savings: float = 0.0
    additional_savings: Dict[str, float] = field(default_factory=dict)

