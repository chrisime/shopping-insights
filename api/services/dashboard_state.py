"""Backend dashboard state used to build reusable UI payloads."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Protocol

from api.services.dashboard_errors import DashboardError, missing_database_error, no_receipts_error
from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


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
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TopItemRow], int]:
        ...

    def top_items_by_spend(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TopItemRow], int]:
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
    search: str | None
    page: int
    available_kpis: BasicKPIs
    kpis: BasicKPIs
    bonus_kpis: RetailerBonusKPIs
    derived: DashboardDerivedMetrics
    time_series: list[TimeSeriesRow]
    weekday: list[WeekdayRow]
    top_items: list[TopItemRow]
    top_items_total: int
    min_date: Any
    max_date: Any
    error: DashboardError | None = None
    rewe_kpis: BasicKPIs | None = None
    lidl_kpis: BasicKPIs | None = None
    rewe_bonus_kpis: RetailerBonusKPIs | None = None
    lidl_bonus_kpis: RetailerBonusKPIs | None = None


def build_dashboard_state(
    provider: DashboardMetricsProvider,
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    time_granularity: str,
    spending_view: str,
    top_view: str,
    top_limit: int,
    search: str | None = None,
    page: int = 1,
) -> DashboardState:
    normalized_retailer = retailer.lower() if retailer else None
    try:
        available_kpis = provider.basic_kpis(retailer=normalized_retailer)
        kpis = provider.basic_kpis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
        if kpis.total_receipts == 0:
            return _empty_no_receipts_state(
                retailer=normalized_retailer,
                start_date=start_date,
                end_date=end_date,
                time_granularity=time_granularity,
                spending_view=spending_view,
                top_view=top_view,
                top_limit=top_limit,
                available_kpis=available_kpis,
            )
        bonus_kpis = provider.retailer_bonus_kpis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
        rewe_kpis = lidl_kpis = None
        rewe_bonus_kpis = lidl_bonus_kpis = None
        if normalized_retailer is None:
            rewe_kpis = provider.basic_kpis(retailer="rewe", start_date=start_date, end_date=end_date)
            lidl_kpis = provider.basic_kpis(retailer="lidl", start_date=start_date, end_date=end_date)
            rewe_bonus_kpis = provider.retailer_bonus_kpis(retailer="rewe", start_date=start_date, end_date=end_date)
            lidl_bonus_kpis = provider.retailer_bonus_kpis(retailer="lidl", start_date=start_date, end_date=end_date)
        time_series = _build_time_series(provider, normalized_retailer, start_date, end_date, time_granularity)
        if spending_view == "Kumulativ":
            time_series = _cumulative_time_series(time_series)
        weekday = provider.weekday_analysis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
        top_items, top_items_total = _build_top_items(provider, normalized_retailer, start_date, end_date, top_view, top_limit, search, page)
        derived = _build_derived_metrics(kpis, bonus_kpis)
    except sqlite3.OperationalError:
        return _empty_dashboard_state(
            retailer=normalized_retailer,
            start_date=start_date,
            end_date=end_date,
            time_granularity=time_granularity,
            spending_view=spending_view,
            top_view=top_view,
            top_limit=top_limit,
            error=missing_database_error(),
        )

    return DashboardState(
        retailer=normalized_retailer,
        start_date=start_date,
        end_date=end_date,
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
        search=search,
        page=page,
        available_kpis=available_kpis,
        kpis=kpis,
        bonus_kpis=bonus_kpis,
        rewe_kpis=rewe_kpis,
        lidl_kpis=lidl_kpis,
        rewe_bonus_kpis=rewe_bonus_kpis,
        lidl_bonus_kpis=lidl_bonus_kpis,
        derived=derived,
        time_series=time_series,
        weekday=weekday,
        top_items=top_items,
        top_items_total=top_items_total,
        min_date=available_kpis.min_date,
        max_date=available_kpis.max_date,
    )


def _empty_dashboard_state(
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    time_granularity: str,
    spending_view: str,
    top_view: str,
    top_limit: int,
    error: DashboardError | None = None,
    search: str | None = None,
    page: int = 1,
) -> DashboardState:
    empty_kpis = BasicKPIs(0.0, 0, 0.0, 0.0, 0.0, None, None)
    empty_bonus_kpis = RetailerBonusKPIs(0.0, 0.0, 0.0, 0.0, 0.0)
    empty_derived = DashboardDerivedMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return DashboardState(
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
        search=search,
        page=page,
        available_kpis=empty_kpis,
        kpis=empty_kpis,
        bonus_kpis=empty_bonus_kpis,
        rewe_kpis=None,
        lidl_kpis=None,
        rewe_bonus_kpis=None,
        lidl_bonus_kpis=None,
        derived=empty_derived,
        time_series=[],
        weekday=[],
        top_items=[],
        top_items_total=0,
        min_date=None,
        max_date=None,
        error=error,
    )


def _empty_no_receipts_state(
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    time_granularity: str,
    spending_view: str,
    top_view: str,
    top_limit: int,
    available_kpis: BasicKPIs,
    search: str | None = None,
    page: int = 1,
) -> DashboardState:
    empty_kpis = BasicKPIs(0.0, 0, 0.0, 0.0, 0.0, available_kpis.min_date, available_kpis.max_date)
    empty_bonus_kpis = RetailerBonusKPIs(0.0, 0.0, 0.0, 0.0, 0.0)
    empty_derived = DashboardDerivedMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    return DashboardState(
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
        search=search,
        page=page,
        available_kpis=available_kpis,
        kpis=empty_kpis,
        bonus_kpis=empty_bonus_kpis,
        rewe_kpis=None,
        lidl_kpis=None,
        rewe_bonus_kpis=None,
        lidl_bonus_kpis=None,
        derived=empty_derived,
        time_series=[],
        weekday=[],
        top_items=[],
        top_items_total=0,
        min_date=available_kpis.min_date,
        max_date=available_kpis.max_date,
        error=no_receipts_error(),
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


def _cumulative_time_series(time_series: list[TimeSeriesRow]) -> list[TimeSeriesRow]:
    running_total = 0.0
    cumulative: list[TimeSeriesRow] = []
    for row in time_series:
        running_total += row.total_spent
        cumulative.append(
            TimeSeriesRow(period=row.period, total_spent=running_total, receipt_count=row.receipt_count)
        )
    return cumulative


def _build_top_items(
    provider: DashboardMetricsProvider,
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    top_view: str,
    top_limit: int,
    search: str | None = None,
    page: int = 1,
) -> tuple[list[TopItemRow], int]:
    page_size = top_limit
    if top_view == "Ausgaben":
        return provider.top_items_by_spend(
            retailer=retailer, start_date=start_date, end_date=end_date,
            search=search, page=page, page_size=page_size,
        )
    return provider.top_items_by_quantity(
        retailer=retailer, start_date=start_date, end_date=end_date,
        search=search, page=page, page_size=page_size,
    )


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
