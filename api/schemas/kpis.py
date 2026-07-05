"""Pydantic schemas for KPI endpoints."""

from typing import Optional

from pydantic import BaseModel


class KpiSummary(BaseModel):
    total_spent: float
    total_receipts: int
    avg_receipt: float
    total_discount: float
    total_saved_deposit: float
    min_date: Optional[str]
    max_date: Optional[str]


class KpiSummaryResponse(BaseModel):
    data: KpiSummary


class KpiBonus(BaseModel):
    rewe_bonus_collected: float
    rewe_bonus_balance: float
    rewe_bonus_redeemed: float
    lidlplus_discount: float
    sticker_discount: float


class KpiBonusResponse(BaseModel):
    data: KpiBonus


class TimeSeriesRow(BaseModel):
    period: str
    total_spent: float
    receipt_count: int


class KpiTrendResponse(BaseModel):
    data: list[TimeSeriesRow]


class TopItemRow(BaseModel):
    name: str
    total_quantity: float
    total_spent: float
    purchase_count: int
    unit: str


class KpiTopItemsResponse(BaseModel):
    data: list[TopItemRow]


class WeekdayRow(BaseModel):
    weekday: int
    weekday_name: str
    trip_count: int
    avg_spent: float
    total_spent: float


class KpiWeekdayResponse(BaseModel):
    data: list[WeekdayRow]
