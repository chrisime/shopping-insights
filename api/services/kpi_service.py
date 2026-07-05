"""Service functions for KPI endpoints."""

from typing import Any, Optional

from metrics import MetricsStore

from api.schemas.kpis import KpiBonus, KpiSummary, TimeSeriesRow, TopItemRow, WeekdayRow


def get_summary(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> KpiSummary:
    kpis = MetricsStore().basic_kpis(
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
    )
    return KpiSummary(
        total_spent=kpis.total_spent,
        total_receipts=kpis.total_receipts,
        avg_receipt=kpis.avg_receipt,
        total_discount=kpis.total_discount,
        total_saved_deposit=kpis.total_saved_deposit,
        min_date=kpis.min_date,
        max_date=kpis.max_date,
    )


def get_bonus(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> KpiBonus:
    bonus = MetricsStore().retailer_bonus_kpis(
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
    )
    return KpiBonus(
        rewe_bonus_collected=bonus.rewe_bonus_collected,
        rewe_bonus_balance=bonus.rewe_bonus_balance,
        rewe_bonus_redeemed=bonus.rewe_bonus_redeemed,
        lidlplus_discount=bonus.lidlplus_discount,
        sticker_discount=bonus.sticker_discount,
    )


def get_trend(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "day",
) -> list[dict[str, Any]]:
    store = MetricsStore()
    if granularity == "month":
        rows = store.spending_by_month(retailer=retailer, start_date=start_date, end_date=end_date)
    elif granularity == "year":
        rows = store.spending_by_year(retailer=retailer, start_date=start_date, end_date=end_date)
    else:
        rows = store.spending_by_day(retailer=retailer, start_date=start_date, end_date=end_date)
    return [row.__dict__ for row in rows]


def get_top_items(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort: str = "quantity",
    limit: int = 20,
) -> list[dict[str, Any]]:
    store = MetricsStore()
    if sort == "spend":
        rows = store.top_items_by_spend(
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    else:
        rows = store.top_items_by_quantity(
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    return [row.__dict__ for row in rows]


def get_weekday(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    rows = MetricsStore().weekday_analysis(retailer=retailer, start_date=start_date, end_date=end_date)
    return [row.__dict__ for row in rows]
