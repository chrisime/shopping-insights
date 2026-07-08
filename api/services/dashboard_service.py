"""Dashboard service layer for the Vue payload."""

from __future__ import annotations

from storage.kpi_store import MetricsStore

from api.services.dashboard_state import build_dashboard_state
from api.services.schema import VueDashboardPayload
from api.services.ui_model import build_dashboard_page_model


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
        search: str | None = None,
        page: int = 1,
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
            search=search,
            page=page,
        )
        model = build_dashboard_page_model(state)
        return VueDashboardPayload.from_page_model(model)
