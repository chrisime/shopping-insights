"""SQLite-backed KPI query store."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional

from config import storage_config
from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


def _connect() -> sqlite3.Connection:
    db_path = Path(storage_config.SQLITE_RECEIPTS_DB_FILE)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _retailer_filter(retailer: Optional[str]) -> tuple[str, tuple]:
    if retailer is None:
        return "", ()
    return "AND s.retailer_code = ?", (retailer.lower(),)


class MetricsStore:
    """Read-only query interface for dashboard KPIs."""

    def basic_kpis(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> BasicKPIs:
        where_parts = ["WHERE 1=1"]
        params: list = []

        retailer_clause, retailer_params = _retailer_filter(retailer)
        if retailer_clause:
            where_parts.append(retailer_clause)
            params.extend(retailer_params)

        if start_date:
            where_parts.append("AND p.purchase_date >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("AND p.purchase_date <= ?")
            params.append(end_date)

        where = " ".join(where_parts)

        sql = f"""
            SELECT
                COALESCE(SUM(p.total_price), 0) AS total_spent,
                COUNT(p.id) AS total_receipts,
                COALESCE(AVG(p.total_price), 0) AS avg_receipt,
                COALESCE(SUM(p.discount), 0) AS total_discount,
                COALESCE(SUM(p.saved_deposit), 0) AS total_saved_deposit,
                MIN(p.purchase_date) AS min_date,
                MAX(p.purchase_date) AS max_date
            FROM purchase p
            JOIN store s ON s.id = p.store_id
            {where}
        """

        with closing(_connect()) as conn:
            row = conn.execute(sql, tuple(params)).fetchone()

        return BasicKPIs(
            total_spent=float(row["total_spent"]),
            total_receipts=int(row["total_receipts"]),
            avg_receipt=float(row["avg_receipt"]),
            total_discount=float(row["total_discount"]),
            total_saved_deposit=float(row["total_saved_deposit"]),
            min_date=row["min_date"],
            max_date=row["max_date"],
        )

    def retailer_bonus_kpis(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> RetailerBonusKPIs:
        date_parts = []
        date_params: list = []
        if start_date:
            date_parts.append("AND p.purchase_date >= ?")
            date_params.append(start_date)
        if end_date:
            date_parts.append("AND p.purchase_date <= ?")
            date_params.append(end_date)
        date_clause = " ".join(date_parts)

        rewe_bonus_collected = 0.0
        rewe_bonus_balance = 0.0
        rewe_bonus_redeemed = 0.0

        if retailer is None or retailer == "rewe":
            sql_rewe = f"""
                SELECT
                    COALESCE(SUM(pr.rewe_bonus_amount), 0) AS bonus_collected,
                    COALESCE(SUM(pr.rewe_bonus_discount), 0) AS bonus_redeemed
                FROM purchase_rewe pr
                JOIN purchase p ON p.id = pr.purchase_id
                WHERE 1=1 {date_clause}
            """
            with closing(_connect()) as conn:
                row = conn.execute(sql_rewe, tuple(date_params)).fetchone()
                rewe_bonus_collected = float(row["bonus_collected"])
                rewe_bonus_redeemed = float(row["bonus_redeemed"])

                sql_balance = f"""
                    SELECT pr.rewe_bonus_total_amount
                    FROM purchase_rewe pr
                    JOIN purchase p ON p.id = pr.purchase_id
                    WHERE 1=1 {date_clause}
                    ORDER BY p.purchase_date DESC
                    LIMIT 1
                """
                balance_row = conn.execute(sql_balance, tuple(date_params)).fetchone()
                if balance_row:
                    rewe_bonus_balance = float(balance_row["rewe_bonus_total_amount"])

        lidlplus_discount = 0.0
        sticker_discount = 0.0

        if retailer is None or retailer == "lidl":
            sql_lidl = f"""
                SELECT
                    COALESCE(SUM(pl.lidlplus_discount), 0) AS lidlplus,
                    COALESCE(SUM(pl.sticker_discount), 0) AS sticker
                FROM purchase_lidl pl
                JOIN purchase p ON p.id = pl.purchase_id
                WHERE 1=1 {date_clause}
            """
            with closing(_connect()) as conn:
                row = conn.execute(sql_lidl, tuple(date_params)).fetchone()
                lidlplus_discount = float(row["lidlplus"])
                sticker_discount = float(row["sticker"])

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
        where_parts = ["WHERE p.total_price IS NOT NULL"]
        params: list = []

        retailer_clause, retailer_params = _retailer_filter(retailer)
        if retailer_clause:
            where_parts.append(retailer_clause)
            params.extend(retailer_params)

        if start_date:
            where_parts.append("AND p.purchase_date >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("AND p.purchase_date <= ?")
            params.append(end_date)

        where = " ".join(where_parts)

        sql = f"""
            SELECT
                DATE(p.purchase_date) AS period,
                SUM(p.total_price) AS total_spent,
                COUNT(p.id) AS receipt_count
            FROM purchase p
            JOIN store s ON s.id = p.store_id
            {where}
            GROUP BY DATE(p.purchase_date)
            ORDER BY period
        """

        with closing(_connect()) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            TimeSeriesRow(
                period=str(row["period"]),
                total_spent=float(row["total_spent"]),
                receipt_count=int(row["receipt_count"]),
            )
            for row in rows
        ]

    def spending_by_month(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[TimeSeriesRow]:
        where_parts = ["WHERE p.total_price IS NOT NULL"]
        params: list = []

        retailer_clause, retailer_params = _retailer_filter(retailer)
        if retailer_clause:
            where_parts.append(retailer_clause)
            params.extend(retailer_params)

        if start_date:
            where_parts.append("AND p.purchase_date >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("AND p.purchase_date <= ?")
            params.append(end_date)

        where = " ".join(where_parts)

        sql = f"""
            SELECT
                STRFTIME('%Y-%m', p.purchase_date) AS period,
                SUM(p.total_price) AS total_spent,
                COUNT(p.id) AS receipt_count
            FROM purchase p
            JOIN store s ON s.id = p.store_id
            {where}
            GROUP BY STRFTIME('%Y-%m', p.purchase_date)
            ORDER BY period
        """

        with closing(_connect()) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            TimeSeriesRow(
                period=str(row["period"]),
                total_spent=float(row["total_spent"]),
                receipt_count=int(row["receipt_count"]),
            )
            for row in rows
        ]

    def spending_by_year(
        self,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[TimeSeriesRow]:
        where_parts = ["WHERE p.total_price IS NOT NULL"]
        params: list = []

        retailer_clause, retailer_params = _retailer_filter(retailer)
        if retailer_clause:
            where_parts.append(retailer_clause)
            params.extend(retailer_params)

        if start_date:
            where_parts.append("AND p.purchase_date >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("AND p.purchase_date <= ?")
            params.append(end_date)

        where = " ".join(where_parts)

        sql = f"""
            SELECT
                STRFTIME('%Y', p.purchase_date) AS period,
                SUM(p.total_price) AS total_spent,
                COUNT(p.id) AS receipt_count
            FROM purchase p
            JOIN store s ON s.id = p.store_id
            {where}
            GROUP BY STRFTIME('%Y', p.purchase_date)
            ORDER BY period
        """

        with closing(_connect()) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            TimeSeriesRow(
                period=str(row["period"]),
                total_spent=float(row["total_spent"]),
                receipt_count=int(row["receipt_count"]),
            )
            for row in rows
        ]

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
        where_parts = ["WHERE 1=1"]
        params: list = []

        retailer_clause, retailer_params = _retailer_filter(retailer)
        if retailer_clause:
            where_parts.append(retailer_clause)
            params.extend(retailer_params)

        if start_date:
            where_parts.append("AND p.purchase_date >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("AND p.purchase_date <= ?")
            params.append(end_date)

        where_parts.append("AND UPPER(pi.name) NOT LIKE '%PFAND%'")

        if search:
            where_parts.append("AND UPPER(pi.name) LIKE ?")
            params.append(f"%{search.upper()}%")

        where = " ".join(where_parts)

        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM (
                SELECT 1
                FROM purchase_item pi
                JOIN purchase p ON p.id = pi.purchase_id
                JOIN store s ON s.id = p.store_id
                {where}
                GROUP BY UPPER(pi.name), pi.unit
            )
        """

        sql = f"""
            SELECT
                pi.name,
                SUM(pi.quantity) AS total_quantity,
                SUM(pi.price * pi.quantity) AS total_spent,
                COUNT(DISTINCT p.id) AS purchase_count,
                pi.unit
            FROM purchase_item pi
            JOIN purchase p ON p.id = pi.purchase_id
            JOIN store s ON s.id = p.store_id
            {where}
            GROUP BY UPPER(pi.name), pi.unit
            ORDER BY {order_col} DESC
            LIMIT ? OFFSET ?
        """
        offset = (page - 1) * page_size
        data_params = list(params) + [page_size, offset]

        with closing(_connect()) as conn:
            total = conn.execute(count_sql, tuple(params)).fetchone()["total"]
            rows = conn.execute(sql, tuple(data_params)).fetchall()

        return [
            TopItemRow(
                name=str(row["name"]),
                total_quantity=float(row["total_quantity"]),
                total_spent=float(row["total_spent"]),
                purchase_count=int(row["purchase_count"]),
                unit=str(row["unit"]),
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
        where_parts = ["WHERE p.total_price IS NOT NULL"]
        params: list = []

        retailer_clause, retailer_params = _retailer_filter(retailer)
        if retailer_clause:
            where_parts.append(retailer_clause)
            params.extend(retailer_params)

        if start_date:
            where_parts.append("AND p.purchase_date >= ?")
            params.append(start_date)
        if end_date:
            where_parts.append("AND p.purchase_date <= ?")
            params.append(end_date)

        where = " ".join(where_parts)

        sql = f"""
            SELECT
                CAST(STRFTIME('%w', p.purchase_date) AS INTEGER) AS dow_raw,
                COUNT(p.id) AS trip_count,
                AVG(p.total_price) AS avg_spent,
                SUM(p.total_price) AS total_spent
            FROM purchase p
            JOIN store s ON s.id = p.store_id
            {where}
            GROUP BY dow_raw
            ORDER BY dow_raw
        """

        weekday_names = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"]
        remap = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}

        with closing(_connect()) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        results = []
        for row in rows:
            dow_raw = int(row["dow_raw"])
            german_idx = remap[dow_raw]
            results.append(
                WeekdayRow(
                    weekday=german_idx,
                    weekday_name=weekday_names[dow_raw],
                    trip_count=int(row["trip_count"]),
                    avg_spent=float(row["avg_spent"]),
                    total_spent=float(row["total_spent"]),
                )
            )

        results.sort(key=lambda r: r.weekday)
        return results
