"""Dashboard data providers for DB-backed and API-backed access."""

from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urljoin

import requests

from metrics import BasicKPIs, MetricsStore, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


class DbDashboardDataProvider:
    def __init__(self, store: MetricsStore | None = None) -> None:
        self._store = store or MetricsStore()

    def basic_kpis(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> BasicKPIs:
        return self._store.basic_kpis(retailer=retailer, start_date=start_date, end_date=end_date)

    def retailer_bonus_kpis(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> RetailerBonusKPIs:
        return self._store.retailer_bonus_kpis(retailer=retailer, start_date=start_date, end_date=end_date)

    def spending_by_day(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[TimeSeriesRow]:
        return self._store.spending_by_day(retailer=retailer, start_date=start_date, end_date=end_date)

    def spending_by_month(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[TimeSeriesRow]:
        return self._store.spending_by_month(retailer=retailer, start_date=start_date, end_date=end_date)

    def spending_by_year(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[TimeSeriesRow]:
        return self._store.spending_by_year(retailer=retailer, start_date=start_date, end_date=end_date)

    def top_items_by_quantity(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 20) -> list[TopItemRow]:
        return self._store.top_items_by_quantity(retailer=retailer, start_date=start_date, end_date=end_date, limit=limit)

    def top_items_by_spend(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 20) -> list[TopItemRow]:
        return self._store.top_items_by_spend(retailer=retailer, start_date=start_date, end_date=end_date, limit=limit)

    def weekday_analysis(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[WeekdayRow]:
        return self._store.weekday_analysis(retailer=retailer, start_date=start_date, end_date=end_date)


class ApiDashboardDataProvider:
    def __init__(self, base_url: str, session: requests.Session | None = None, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/") + "/"
        self._session = session or requests.Session()
        self._timeout = timeout

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict:
        response = self._session.get(urljoin(self._base_url, path.lstrip("/")), params=params, timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    def basic_kpis(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> BasicKPIs:
        payload = self._get("/kpis/summary", self._params(retailer=retailer, start_date=start_date, end_date=end_date))
        return BasicKPIs(**payload["data"])

    def retailer_bonus_kpis(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> RetailerBonusKPIs:
        payload = self._get("/kpis/bonus", self._params(retailer=retailer, start_date=start_date, end_date=end_date))
        return RetailerBonusKPIs(**payload["data"])

    def spending_by_day(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[TimeSeriesRow]:
        payload = self._get("/kpis/trend", self._params(retailer=retailer, start_date=start_date, end_date=end_date, granularity="day"))
        return [TimeSeriesRow(**row) for row in payload["data"]]

    def spending_by_month(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[TimeSeriesRow]:
        payload = self._get("/kpis/trend", self._params(retailer=retailer, start_date=start_date, end_date=end_date, granularity="month"))
        return [TimeSeriesRow(**row) for row in payload["data"]]

    def spending_by_year(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[TimeSeriesRow]:
        payload = self._get("/kpis/trend", self._params(retailer=retailer, start_date=start_date, end_date=end_date, granularity="year"))
        return [TimeSeriesRow(**row) for row in payload["data"]]

    def top_items_by_quantity(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 20) -> list[TopItemRow]:
        payload = self._get("/kpis/top-items", self._params(retailer=retailer, start_date=start_date, end_date=end_date, sort="quantity", limit=limit))
        return [TopItemRow(**row) for row in payload["data"]]

    def top_items_by_spend(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 20) -> list[TopItemRow]:
        payload = self._get("/kpis/top-items", self._params(retailer=retailer, start_date=start_date, end_date=end_date, sort="spend", limit=limit))
        return [TopItemRow(**row) for row in payload["data"]]

    def weekday_analysis(self, retailer: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[WeekdayRow]:
        payload = self._get("/kpis/weekday", self._params(retailer=retailer, start_date=start_date, end_date=end_date))
        return [WeekdayRow(**row) for row in payload["data"]]

    @staticmethod
    def _params(**kwargs: object) -> dict[str, str]:
        return {key: str(value) for key, value in kwargs.items() if value is not None}


def get_dashboard_data_provider() -> DbDashboardDataProvider | ApiDashboardDataProvider:
    api_base_url = os.getenv("API_BASE_URL", "").strip()
    if api_base_url:
        return ApiDashboardDataProvider(api_base_url)
    return DbDashboardDataProvider()
