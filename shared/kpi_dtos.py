"""Shared KPI DTOs used by the dashboard and API layers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BasicKPIs:
    """Grundkennzahlen for a retailer or all retailers."""

    total_spent: float
    total_receipts: int
    avg_receipt: float
    total_discount: float
    total_saved_deposit: float
    min_date: Optional[str]
    max_date: Optional[str]


@dataclass(frozen=True)
class RetailerBonusKPIs:
    """Retailer-specific loyalty/bonus KPIs."""

    rewe_bonus_collected: float
    rewe_bonus_balance: float
    rewe_bonus_redeemed: float
    lidlplus_discount: float
    sticker_discount: float


@dataclass(frozen=True)
class TimeSeriesRow:
    """One row in a time-series aggregation."""

    period: str
    total_spent: float
    receipt_count: int


@dataclass(frozen=True)
class TopItemRow:
    """One row in a top-items ranking."""

    name: str
    total_quantity: float
    total_spent: float
    purchase_count: int
    unit: str


@dataclass(frozen=True)
class WeekdayRow:
    """Aggregated metrics per weekday (0=Monday … 6=Sunday)."""

    weekday: int
    weekday_name: str
    trip_count: int
    avg_spent: float
    total_spent: float
