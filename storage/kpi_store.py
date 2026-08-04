"""SQLAlchemy Core based SQLite KPI query store."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, Row, Select, distinct, func, select

from config import storage_config
from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow

from .database import connect
from .sqlite_schema import (
    purchase_item_table,
    purchase_lidl_table,
    purchase_rewe_table,
    purchase_table,
    store_table,
)


def _apply_filters(
    stmt: Select,
    retailer: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Select:
    if retailer:
        stmt = stmt.where(store_table.c.retailer_code == retailer.lower())
    if start_date:
        stmt = stmt.where(purchase_table.c.purchase_date >= start_date)
    if end_date:
        stmt = stmt.where(purchase_table.c.purchase_date <= end_date)
    return stmt


def _apply_date_filters(
    stmt: Select,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Select:
    if start_date:
        stmt = stmt.where(purchase_table.c.purchase_date >= start_date)
    if end_date:
        stmt = stmt.where(purchase_table.c.purchase_date <= end_date)
    return stmt


def _map_time_series_row(row: Row) -> TimeSeriesRow:
    return TimeSeriesRow(
        period=str(row._mapping["period"]),
        total_spent=float(row._mapping["total_spent"]),
        receipt_count=int(row._mapping["receipt_count"]),
        retailers=row._mapping["retailers"].split(",") if row._mapping["retailers"] else [],
    )


class MetricsStore:
    """Read-only query interface for dashboard KPIs."""

    def basic_kpis(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> BasicKPIs:
        stmt = (
            select(
                func.coalesce(func.sum(purchase_table.c.total_price), 0).label("total_spent"),
                func.count(purchase_table.c.id).label("total_receipts"),
                func.coalesce(func.avg(purchase_table.c.total_price), 0).label("avg_receipt"),
                func.coalesce(func.sum(purchase_table.c.discount), 0).label("total_discount"),
                func.coalesce(func.sum(purchase_table.c.saved_deposit), 0).label("total_saved_deposit"),
                func.min(purchase_table.c.purchase_date).label("min_date"),
                func.max(purchase_table.c.purchase_date).label("max_date"),
            )
            .select_from(purchase_table)
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
        )
        stmt = _apply_filters(stmt, retailer, start_date, end_date)

        with connect() as connection:
            row = connection.execute(stmt).one()

        return BasicKPIs(
            total_spent=float(row._mapping["total_spent"]),
            total_receipts=int(row._mapping["total_receipts"]),
            avg_receipt=float(row._mapping["avg_receipt"]),
            total_discount=float(row._mapping["total_discount"]),
            total_saved_deposit=float(row._mapping["total_saved_deposit"]),
            min_date=row._mapping["min_date"],
            max_date=row._mapping["max_date"],
        )

    def retailer_bonus_kpis(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> RetailerBonusKPIs:
        rewe_bonus_collected = 0.0
        rewe_bonus_balance = 0.0
        rewe_bonus_redeemed = 0.0

        with connect() as connection:
            if retailer is None or retailer == "rewe":
                rewe_stmt = (
                    select(
                        func.coalesce(func.sum(purchase_rewe_table.c.rewe_bonus_amount), 0).label("bonus_collected"),
                        func.coalesce(func.sum(purchase_rewe_table.c.rewe_bonus_discount), 0).label("bonus_redeemed"),
                    )
                    .select_from(purchase_rewe_table)
                    .join(purchase_table, purchase_table.c.id == purchase_rewe_table.c.purchase_id)
                )
                rewe_stmt = _apply_date_filters(rewe_stmt, start_date, end_date)
                row = connection.execute(rewe_stmt).one()
                rewe_bonus_collected = float(row._mapping["bonus_collected"])
                rewe_bonus_redeemed = float(row._mapping["bonus_redeemed"])

                balance_stmt = (
                    select(purchase_rewe_table.c.rewe_bonus_total_amount)
                    .select_from(purchase_rewe_table)
                    .join(purchase_table, purchase_table.c.id == purchase_rewe_table.c.purchase_id)
                    .order_by(purchase_table.c.purchase_date.desc())
                    .limit(1)
                )
                balance_stmt = _apply_date_filters(balance_stmt, start_date, end_date)
                balance_row = connection.execute(balance_stmt).fetchone()
                if balance_row is not None:
                    rewe_bonus_balance = float(balance_row._mapping["rewe_bonus_total_amount"])

            lidlplus_discount = 0.0
            sticker_discount = 0.0

            if retailer is None or retailer == "lidl":
                lidl_stmt = (
                    select(
                        func.coalesce(func.sum(purchase_lidl_table.c.lidlplus_discount), 0).label("lidlplus"),
                        func.coalesce(func.sum(purchase_lidl_table.c.sticker_discount), 0).label("sticker"),
                    )
                    .select_from(purchase_lidl_table)
                    .join(purchase_table, purchase_table.c.id == purchase_lidl_table.c.purchase_id)
                )
                lidl_stmt = _apply_date_filters(lidl_stmt, start_date, end_date)
                row = connection.execute(lidl_stmt).one()
                lidlplus_discount = float(row._mapping["lidlplus"])
                sticker_discount = float(row._mapping["sticker"])

        return RetailerBonusKPIs(
            rewe_bonus_collected=rewe_bonus_collected,
            rewe_bonus_balance=rewe_bonus_balance,
            rewe_bonus_redeemed=rewe_bonus_redeemed,
            lidlplus_discount=lidlplus_discount,
            sticker_discount=sticker_discount,
        )

    def spending_by_day(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[TimeSeriesRow]:
        period = func.date(purchase_table.c.purchase_date).label("period")
        return self._spending_by_period(period, retailer, start_date, end_date)

    def spending_by_month(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[TimeSeriesRow]:
        period = func.strftime("%Y-%m", purchase_table.c.purchase_date).label("period")
        return self._spending_by_period(period, retailer, start_date, end_date)

    def spending_by_year(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[TimeSeriesRow]:
        period = func.strftime("%Y", purchase_table.c.purchase_date).label("period")
        return self._spending_by_period(period, retailer, start_date, end_date)

    def _spending_by_period(
        self,
        period,
        retailer: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> list[TimeSeriesRow]:
        stmt = (
            select(
                period,
                func.sum(purchase_table.c.total_price).label("total_spent"),
                func.count(purchase_table.c.id).label("receipt_count"),
                func.group_concat(distinct(store_table.c.retailer_code)).label("retailers"),
            )
            .select_from(purchase_table)
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(purchase_table.c.total_price.is_not(None))
        )
        stmt = _apply_filters(stmt, retailer, start_date, end_date)
        stmt = stmt.group_by(period).order_by(period)

        with connect() as connection:
            rows = connection.execute(stmt).fetchall()

        return [_map_time_series_row(row) for row in rows]

    def _top_items_query(
        self,
        order_col: str,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TopItemRow], int]:
        total_quantity = func.sum(purchase_item_table.c.quantity).label("total_quantity")
        total_spent = func.sum(purchase_item_table.c.price * purchase_item_table.c.quantity).label("total_spent")
        order_expr = total_quantity if order_col == "total_quantity" else total_spent

        base_stmt = (
            select(1)
            .select_from(purchase_item_table)
            .join(purchase_table, purchase_table.c.id == purchase_item_table.c.purchase_id)
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(func.upper(purchase_item_table.c.name).notlike("%PFAND%"))
        )
        if search:
            base_stmt = base_stmt.where(func.upper(purchase_item_table.c.name).like(f"%{search.upper()}%"))
        base_stmt = _apply_filters(base_stmt, retailer, start_date, end_date)

        count_subquery = base_stmt.group_by(
            func.upper(purchase_item_table.c.name), purchase_item_table.c.unit
        ).subquery()
        count_stmt = select(func.count()).select_from(count_subquery)

        data_stmt = (
            select(
                purchase_item_table.c.name,
                total_quantity,
                total_spent,
                func.count(distinct(purchase_table.c.id)).label("purchase_count"),
                purchase_item_table.c.unit,
            )
            .select_from(purchase_item_table)
            .join(purchase_table, purchase_table.c.id == purchase_item_table.c.purchase_id)
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(func.upper(purchase_item_table.c.name).notlike("%PFAND%"))
        )
        if search:
            data_stmt = data_stmt.where(func.upper(purchase_item_table.c.name).like(f"%{search.upper()}%"))
        data_stmt = _apply_filters(data_stmt, retailer, start_date, end_date)
        offset = (page - 1) * page_size
        data_stmt = (
            data_stmt.group_by(func.upper(purchase_item_table.c.name), purchase_item_table.c.unit)
            .order_by(order_expr.desc())
            .limit(page_size)
            .offset(offset)
        )

        with connect() as connection:
            total = connection.execute(count_stmt).scalar_one()
            rows = connection.execute(data_stmt).fetchall()

        return [
            TopItemRow(
                name=str(row._mapping["name"]),
                total_quantity=float(row._mapping["total_quantity"]),
                total_spent=float(row._mapping["total_spent"]),
                purchase_count=int(row._mapping["purchase_count"]),
                unit=str(row._mapping["unit"]),
            )
            for row in rows
        ], int(total)

    def top_items_by_quantity(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TopItemRow], int]:
        return self._top_items_query(
            "total_quantity",
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            search=search,
            page=page,
            page_size=page_size,
        )

    def top_items_by_spend(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TopItemRow], int]:
        return self._top_items_query(
            "total_spent",
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            search=search,
            page=page,
            page_size=page_size,
        )

    def weekday_analysis(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[WeekdayRow]:
        dow_raw = func.cast(func.strftime("%w", purchase_table.c.purchase_date), Integer).label("dow_raw")
        stmt = (
            select(
                dow_raw,
                func.count(purchase_table.c.id).label("trip_count"),
                func.avg(purchase_table.c.total_price).label("avg_spent"),
                func.sum(purchase_table.c.total_price).label("total_spent"),
            )
            .select_from(purchase_table)
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(purchase_table.c.total_price.is_not(None))
        )
        stmt = _apply_filters(stmt, retailer, start_date, end_date)
        stmt = stmt.group_by(dow_raw).order_by(dow_raw)

        weekday_names = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"]
        remap = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}

        with connect() as connection:
            rows = connection.execute(stmt).fetchall()

        results = []
        for row in rows:
            dow_value = int(row._mapping["dow_raw"])
            german_idx = remap[dow_value]
            results.append(
                WeekdayRow(
                    weekday=german_idx,
                    weekday_name=weekday_names[dow_value],
                    trip_count=int(row._mapping["trip_count"]),
                    avg_spent=float(row._mapping["avg_spent"]),
                    total_spent=float(row._mapping["total_spent"]),
                )
            )

        results.sort(key=lambda r: r.weekday)
        return results
