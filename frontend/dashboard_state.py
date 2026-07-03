"""Backend dashboard state used to build reusable UI payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from metrics import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


class DashboardMetricsProvider(Protocol):
    def basic_kpis(self, retailer: str | None = None, start_date: str | None = None, end_date: str | None = None) -> BasicKPIs:
        ...

    def retailer_bonus_kpis(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> RetailerBonusKPIs:
        ...

    def spending_by_day(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[TimeSeriesRow]:
        ...

    def spending_by_month(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[TimeSeriesRow]:
        ...

    def spending_by_year(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[TimeSeriesRow]:
        ...

    def weekday_analysis(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[WeekdayRow]:
        ...

    def top_items_by_quantity(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20,
    ) -> list[TopItemRow]:
        ...

    def top_items_by_spend(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 20,
    ) -> list[TopItemRow]:
        ...


@dataclass(frozen=True)
class DashboardDerivedMetrics:
    total_before_discount: float
    discount_pct: float
    bonus_redeemed_pct: float
    total_bonus_redeemed: float
    total_savings_no_deposit: float
    total_savings_pct: float
    lidlplus_pct: float
    sticker_pct: float


@dataclass(frozen=True)
class DashboardState:
    retailer: str | None
    start_date: str | None
    end_date: str | None
    time_granularity: str
    spending_view: str
    top_view: str
    top_limit: int
    available_kpis: BasicKPIs
    kpis: BasicKPIs
    bonus_kpis: RetailerBonusKPIs
    derived: DashboardDerivedMetrics
    time_series: list[TimeSeriesRow]
    weekday: list[WeekdayRow]
    top_items: list[TopItemRow]
    min_date: Any
    max_date: Any


def build_dashboard_state(
    provider: DashboardMetricsProvider,
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    time_granularity: str,
    spending_view: str,
    top_view: str,
    top_limit: int,
) -> DashboardState:
    normalized_retailer = retailer.lower() if retailer else None
    available_kpis = provider.basic_kpis(retailer=normalized_retailer)
    kpis = provider.basic_kpis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
    bonus_kpis = provider.retailer_bonus_kpis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
    time_series = _build_time_series(provider, normalized_retailer, start_date, end_date, time_granularity)
    weekday = provider.weekday_analysis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
    top_items = _build_top_items(provider, normalized_retailer, start_date, end_date, top_view, top_limit)
    derived = _build_derived_metrics(kpis, bonus_kpis)

    return DashboardState(
        retailer=normalized_retailer,
        start_date=start_date,
        end_date=end_date,
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
        available_kpis=available_kpis,
        kpis=kpis,
        bonus_kpis=bonus_kpis,
        derived=derived,
        time_series=time_series,
        weekday=weekday,
        top_items=top_items,
        min_date=available_kpis.min_date,
        max_date=available_kpis.max_date,
    )


def _build_time_series(
    provider: DashboardMetricsProvider,
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    time_granularity: str,
) -> list[TimeSeriesRow]:
    if time_granularity == "Täglich":
        return provider.spending_by_day(retailer=retailer, start_date=start_date, end_date=end_date)
    if time_granularity == "Jährlich":
        return provider.spending_by_year(retailer=retailer, start_date=start_date, end_date=end_date)
    return provider.spending_by_month(retailer=retailer, start_date=start_date, end_date=end_date)


def _build_top_items(
    provider: DashboardMetricsProvider,
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    top_view: str,
    top_limit: int,
) -> list[TopItemRow]:
    if top_view == "Ausgaben":
        return provider.top_items_by_spend(retailer=retailer, start_date=start_date, end_date=end_date, limit=top_limit)
    return provider.top_items_by_quantity(retailer=retailer, start_date=start_date, end_date=end_date, limit=top_limit)


def _build_derived_metrics(kpis: BasicKPIs, bonus_kpis: RetailerBonusKPIs) -> DashboardDerivedMetrics:
    total_bonus_redeemed = bonus_kpis.rewe_bonus_redeemed + bonus_kpis.lidlplus_discount + bonus_kpis.sticker_discount
    total_before_discount = kpis.total_spent + kpis.total_discount + total_bonus_redeemed
    discount_pct = _pct(kpis.total_discount, kpis.total_spent)
    bonus_redeemed_pct = _pct(total_bonus_redeemed, kpis.total_spent)
    total_savings_no_deposit = kpis.total_discount + total_bonus_redeemed
    total_savings_pct = _pct(total_savings_no_deposit, kpis.total_spent)
    lidlplus_pct = _pct(bonus_kpis.lidlplus_discount, kpis.total_spent)
    sticker_pct = _pct(bonus_kpis.sticker_discount, kpis.total_spent)
    return DashboardDerivedMetrics(
        total_before_discount=total_before_discount,
        discount_pct=discount_pct,
        bonus_redeemed_pct=bonus_redeemed_pct,
        total_bonus_redeemed=total_bonus_redeemed,
        total_savings_no_deposit=total_savings_no_deposit,
        total_savings_pct=total_savings_pct,
        lidlplus_pct=lidlplus_pct,
        sticker_pct=sticker_pct,
    )


def _pct(value: float, total: float) -> float:
    if not total:
        return 0.0
    return round((value / total) * 100, 2)
