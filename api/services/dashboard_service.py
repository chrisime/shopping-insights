"""Dashboard service layer for the Vue payload."""

from __future__ import annotations

from storage.kpi_store import MetricsStore

from frontend.dashboard_state import build_dashboard_state
from frontend.schema import VueDashboardPayload
from frontend.ui_model import build_dashboard_page_model


class DashboardService:
    def __init__(self, store: MetricsStore | None = None) -> None:
        self._store = store or MetricsStore()

    def get_vue_dashboard_payload(
        self,
        retailer: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        time_granularity: str = "Täglich",
        spending_view: str = "Absolut",
        top_view: str = "Menge",
        top_limit: int = 20,
    ) -> VueDashboardPayload:
        state = build_dashboard_state(
            self._store,
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            time_granularity=time_granularity,
            spending_view=spending_view,
            top_view=top_view,
            top_limit=top_limit,
        )
        page = build_dashboard_page_model(state)
        return VueDashboardPayload.from_page_model(page)
