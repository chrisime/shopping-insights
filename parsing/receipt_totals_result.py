"""Shared totals result types for receipt parsers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class ReceiptTotalsResult:
    """Common totals result used by Lidl and REWE extractors."""

    amount_saved: Optional[float]
    saved_deposit: Optional[float]
    total_price: Optional[float]
    additional_savings: Dict[str, float] = field(default_factory=dict)

