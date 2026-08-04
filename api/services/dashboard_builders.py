"""Dashboard builders — pure functions that derive dashboard state and page models."""

from __future__ import annotations

import sqlite3
from typing import Any

from api.services.dashboard_errors import missing_database_error, no_receipts_error
from api.services.dashboard_models import (
    DashboardDerivedMetrics,
    DashboardPageModel,
    DashboardSection,
    DashboardState,
)
from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow
from storage.kpi_store import MetricsStore


# ── Helpers ───────────────────────────────────────────────────────────

def _pct(value: float, total: float) -> float:
    if not total:
        return 0.0
    return round((value / total) * 100, 2)


def _date_text(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _is_empty_state(state: DashboardState) -> bool:
    return state.error is not None


def _retailer_spent(state: DashboardState, retailer: str) -> float:
    if state.retailer == retailer:
        return state.kpis.total_spent
    if retailer == "rewe" and state.rewe_kpis is not None:
        return state.rewe_kpis.total_spent
    if retailer == "lidl" and state.lidl_kpis is not None:
        return state.lidl_kpis.total_spent
    return state.kpis.total_spent


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


def _build_time_series(
    provider: MetricsStore,
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
    provider: MetricsStore,
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


def _build_kpi_metrics(state: DashboardState) -> dict[str, float]:
    metrics: dict[str, float] = {
        "spendings": state.kpis.total_spent,
        "spendings_without_discount": state.derived.total_before_discount,
        "receipt_count": float(state.kpis.total_receipts),
        "avg_receipt_amount": state.kpis.avg_receipt,
        "saved_deposit": state.kpis.total_saved_deposit,
        "total_savings": state.derived.total_savings_no_deposit,
        "total_savings_pct": state.derived.total_savings_pct,
    }

    if state.retailer in (None, "rewe"):
        rewe_bonus = (
            state.rewe_bonus_kpis
            if state.retailer is None and state.rewe_bonus_kpis is not None
            else state.bonus_kpis
        )
        rewe_regular = (
            state.rewe_kpis.total_discount
            if state.retailer is None and state.rewe_kpis is not None
            else state.kpis.total_discount
        )
        rewe_bonus_open = max(0.0, rewe_bonus.rewe_bonus_collected - rewe_bonus.rewe_bonus_redeemed)
        metrics["rewe_discount_amount"] = rewe_regular
        metrics["rewe_discount_pct"] = _pct(rewe_regular, _retailer_spent(state, "rewe"))
        metrics["rewe_bonus_collected"] = rewe_bonus.rewe_bonus_collected
        metrics["rewe_bonus_balance"] = rewe_bonus.rewe_bonus_balance
        metrics["rewe_bonus_redeemed"] = rewe_bonus.rewe_bonus_redeemed
        metrics["rewe_bonus_open"] = rewe_bonus_open

    if state.retailer in (None, "lidl"):
        lidl_bonus = (
            state.lidl_bonus_kpis
            if state.retailer is None and state.lidl_bonus_kpis is not None
            else state.bonus_kpis
        )
        lidl_regular = (
            state.lidl_kpis.total_discount
            if state.retailer is None and state.lidl_kpis is not None
            else state.kpis.total_discount
        )
        metrics["lidlplus_discount_amount"] = lidl_bonus.lidlplus_discount
        metrics["lidlplus_discount_pct"] = _pct(lidl_bonus.lidlplus_discount, _retailer_spent(state, "lidl"))
        metrics["sticker_discount_amount"] = lidl_bonus.sticker_discount
        metrics["sticker_discount_pct"] = _pct(lidl_bonus.sticker_discount, _retailer_spent(state, "lidl"))
        metrics["lidl_discount_amount"] = lidl_regular
        metrics["lidl_discount_pct"] = _pct(lidl_regular, _retailer_spent(state, "lidl"))

    return metrics


def _empty_dashboard_state(
    retailer: str | None,
    start_date: str | None,
    end_date: str | None,
    time_granularity: str,
    spending_view: str,
    top_view: str,
    top_limit: int,
    error: Any = None,
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


# ── Public Builder Functions ──────────────────────────────────────────

def build_dashboard_state(
    store: MetricsStore,
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    time_granularity: str = "Täglich",
    spending_view: str = "Absolut",
    top_view: str = "Menge",
    top_limit: int = 20,
    search: str | None = None,
    page: int = 1,
) -> DashboardState:
    normalized_retailer = retailer.lower() if retailer else None
    try:
        available_kpis = store.basic_kpis(retailer=normalized_retailer)
        kpis = store.basic_kpis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
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
        bonus_kpis = store.retailer_bonus_kpis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
        rewe_kpis = lidl_kpis = None
        rewe_bonus_kpis = lidl_bonus_kpis = None
        if normalized_retailer is None:
            rewe_kpis = store.basic_kpis(retailer="rewe", start_date=start_date, end_date=end_date)
            lidl_kpis = store.basic_kpis(retailer="lidl", start_date=start_date, end_date=end_date)
            rewe_bonus_kpis = store.retailer_bonus_kpis(retailer="rewe", start_date=start_date, end_date=end_date)
            lidl_bonus_kpis = store.retailer_bonus_kpis(retailer="lidl", start_date=start_date, end_date=end_date)
        time_series = _build_time_series(store, normalized_retailer, start_date, end_date, time_granularity)
        if spending_view == "Kumulativ":
            time_series = _cumulative_time_series(time_series)
        weekday = store.weekday_analysis(retailer=normalized_retailer, start_date=start_date, end_date=end_date)
        top_items, top_items_total = _build_top_items(store, normalized_retailer, start_date, end_date, top_view, top_limit, search, page)
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


def build_dashboard_page_model(state: DashboardState) -> DashboardPageModel:
    if _is_empty_state(state):
        return DashboardPageModel(
            title="Shopping Analyzer Dashboard",
            sections=[],
            min_date=_date_text(state.min_date),
            max_date=_date_text(state.max_date),
            error=state.error,
        )

    sections = [DashboardSection(kind="metrics", title="Kennzahlen", items=[_build_kpi_metrics(state)])]

    sections.extend(
        [
            DashboardSection(
                kind="time_series",
                title="Ausgaben über Zeit",
                items=[
                    {"period": row.period, "total_spent": row.total_spent, "receipt_count": row.receipt_count, "retailers": row.retailers}
                    for row in state.time_series
                ],
            ),
            DashboardSection(
                kind="weekday",
                title="Einkaufsverhalten nach Wochentag",
                items=[
                    {
                        "weekday": row.weekday,
                        "weekday_name": row.weekday_name,
                        "trip_count": row.trip_count,
                        "avg_spent": row.avg_spent,
                        "total_spent": row.total_spent,
                    }
                    for row in state.weekday
                ],
            ),
            DashboardSection(
                kind="top_items",
                title="Top-Artikel",
                items=[
                    {
                        "name": row.name,
                        "total_quantity": row.total_quantity,
                        "total_spent": row.total_spent,
                        "purchase_count": row.purchase_count,
                        "unit": row.unit,
                    }
                    for row in state.top_items
                ],
            ),
        ]
    )

    # append pagination metadata to the top_items section
    if sections and sections[-1].kind == "top_items":
        last = sections[-1]
        sections[-1] = DashboardSection(
            kind="top_items",
            title=last.title,
            items=[
                {**item, "total_count": state.top_items_total, "page": state.page, "page_size": state.top_limit}
                for item in last.items
            ],
        )
    return DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=sections,
        min_date=_date_text(state.min_date),
        max_date=_date_text(state.max_date),
        error=state.error,
    )
