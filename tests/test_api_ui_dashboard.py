from datetime import date


def test_ui_dashboard_endpoint_returns_section_payload(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import ui_service
    from frontend.dashboard_state import DashboardDerivedMetrics, DashboardState
    from frontend.ui_model import DashboardPageModel, DashboardSection
    from metrics import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow

    state = DashboardState(
        retailer="lidl",
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_granularity="Monatlich",
        spending_view="Absolut",
        top_view="Menge",
        top_limit=10,
        available_kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        bonus_kpis=RetailerBonusKPIs(1.0, 2.0, 3.0, 4.0, 5.0),
        derived=DashboardDerivedMetrics(122.0, 10.0, 12.0, 12.0, 22.0, 22.0, 4.0, 5.0),
        time_series=[TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)],
        weekday=[WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)],
        top_items=[TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")],
        min_date=date(2024, 1, 1),
        max_date=date(2024, 1, 31),
    )

    page = DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=[DashboardSection(kind="metrics", title="Kennzahlen", items=[{"label": "A", "value": "1"}])],
    )

    monkeypatch.setattr(ui_service, "build_dashboard_state", lambda *args, **kwargs: state)
    monkeypatch.setattr(ui_service, "build_dashboard_page_model", lambda *_: page)

    response = TestClient(app).get(
        "/ui/dashboard",
        params={
            "retailer": "lidl",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "time_granularity": "Monatlich",
            "spending_view": "Absolut",
            "top_view": "Menge",
            "top_limit": 10,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Shopping Analyzer Dashboard"
    assert response.json()["sections"][0]["kind"] == "metrics"
    assert response.json()["sections"][0]["items"][0]["label"] == "A"
