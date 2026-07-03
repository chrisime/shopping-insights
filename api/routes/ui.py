"""Routes for the dashboard payload used by the Vue frontend."""

from __future__ import annotations

from fastapi import APIRouter

from api.services.ui_service import get_vue_dashboard_payload

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/dashboard")
def read_dashboard(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    time_granularity: str = "Täglich",
    spending_view: str = "Absolut",
    top_view: str = "Menge",
    top_limit: int = 20,
):
    return get_vue_dashboard_payload(
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
    ).to_dict()
