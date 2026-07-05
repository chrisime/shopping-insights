from datetime import date
import sqlite3


def test_build_dashboard_state_turns_kumulativ_time_series_cumulative():
    from frontend.dashboard_state import DashboardDerivedMetrics, build_dashboard_state
    from frontend.ui_model import build_dashboard_page_model
    from metrics import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow

    class DummyProvider:
        def basic_kpis(self, retailer=None, start_date=None, end_date=None):
            return BasicKPIs(25.0, 2, 12.5, 0.0, 0.0, "2024-01-01", "2024-01-31")

        def retailer_bonus_kpis(self, retailer=None, start_date=None, end_date=None):
            return RetailerBonusKPIs(0.0, 0.0, 0.0, 0.0, 0.0)

        def spending_by_month(self, retailer=None, start_date=None, end_date=None):
            return [
                TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1),
                TimeSeriesRow(period="2024-02", total_spent=15.0, receipt_count=1),
            ]

        def spending_by_day(self, retailer=None, start_date=None, end_date=None):
            return []

        def spending_by_year(self, retailer=None, start_date=None, end_date=None):
            return []

        def weekday_analysis(self, retailer=None, start_date=None, end_date=None):
            return [WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)]

        def top_items_by_quantity(self, retailer=None, start_date=None, end_date=None, limit=20):
            return [TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")]

        def top_items_by_spend(self, retailer=None, start_date=None, end_date=None, limit=20):
            return []

    state = build_dashboard_state(
        DummyProvider(),
        retailer="lidl",
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_granularity="Monatlich",
        spending_view="Kumulativ",
        top_view="Menge",
        top_limit=10,
    )

    page = build_dashboard_page_model(state)
    time_series_section = next(section for section in page.sections if section.kind == "time_series")

    assert [item["total_spent"] for item in time_series_section.items] == [10.0, 25.0]


def test_build_dashboard_page_model_formats_kpis_and_includes_bonus_sections():
    from frontend.dashboard_state import DashboardDerivedMetrics, DashboardState
    from frontend.ui_model import build_dashboard_page_model
    from metrics import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow

    state = DashboardState(
        retailer=None,
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_granularity="Monatlich",
        spending_view="Absolut",
        top_view="Menge",
        top_limit=10,
        available_kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        bonus_kpis=RetailerBonusKPIs(1.0, 2.0, 3.0, 4.0, 5.0),
        derived=DashboardDerivedMetrics(117.0, 10.0, 9.0, 9.0, 19.0, 19.0, 4.0, 5.0),
        time_series=[TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)],
        weekday=[WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)],
        top_items=[TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")],
        min_date=date(2024, 1, 1),
        max_date=date(2024, 1, 31),
    )

    page = build_dashboard_page_model(state).to_dict()

    assert page["min_date"] == "2024-01-01"
    assert page["max_date"] == "2024-01-31"
    metrics = next(section for section in page["sections"] if section["kind"] == "metrics")
    bonus_rewe = next(section for section in page["sections"] if section["kind"] == "bonus_rewe")
    bonus_lidl = next(section for section in page["sections"] if section["kind"] == "bonus_lidl")

    assert metrics["items"][0]["value"] == "€100.00"
    assert metrics["items"][2]["value"] == "4"
    assert bonus_rewe["items"][0]["value"] == "€1.00"
    assert bonus_lidl["items"][1]["value"] == "4.0%"


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
        min_date="2024-01-01",
        max_date="2024-01-31",
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
    assert response.json()["min_date"] == "2024-01-01"
    assert response.json()["max_date"] == "2024-01-31"


def test_ui_dashboard_allows_vite_dev_origin(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.routes import ui as ui_route

    monkeypatch.setattr(
        ui_route,
        "get_vue_dashboard_payload",
        lambda **kwargs: type(
            "Payload",
            (),
            {
                "to_dict": lambda self: {
                    "title": "Shopping Analyzer Dashboard",
                    "sections": [],
                    "min_date": None,
                    "max_date": None,
                }
            },
        )(),
    )

    response = TestClient(app).get("/ui/dashboard", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_build_dashboard_state_returns_empty_payload_when_database_tables_are_missing():
    from frontend.dashboard_state import build_dashboard_state
    from frontend.ui_model import build_dashboard_page_model

    class MissingTableProvider:
        def basic_kpis(self, *args, **kwargs):
            raise sqlite3.OperationalError("no such table: purchase")

        def retailer_bonus_kpis(self, *args, **kwargs):
            raise AssertionError("should not be called")

        def spending_by_day(self, *args, **kwargs):
            raise AssertionError("should not be called")

        def spending_by_month(self, *args, **kwargs):
            raise AssertionError("should not be called")

        def spending_by_year(self, *args, **kwargs):
            raise AssertionError("should not be called")

        def weekday_analysis(self, *args, **kwargs):
            raise AssertionError("should not be called")

        def top_items_by_quantity(self, *args, **kwargs):
            raise AssertionError("should not be called")

        def top_items_by_spend(self, *args, **kwargs):
            raise AssertionError("should not be called")

    state = build_dashboard_state(
        MissingTableProvider(),
        retailer=None,
        start_date=None,
        end_date=None,
        time_granularity="Täglich",
        spending_view="Absolut",
        top_view="Menge",
        top_limit=20,
    )
    page = build_dashboard_page_model(state).to_dict()

    assert page == {
        "title": "Shopping Analyzer Dashboard",
        "sections": [],
        "min_date": None,
        "max_date": None,
        "error": {"error_code": 101, "detail": "missing_database"},
    }


def test_build_dashboard_state_returns_no_receipts_error_for_empty_database():
    from frontend.dashboard_state import build_dashboard_state
    from frontend.ui_model import build_dashboard_page_model
    from metrics import BasicKPIs, RetailerBonusKPIs

    class EmptyProvider:
        def basic_kpis(self, retailer=None, start_date=None, end_date=None):
            return BasicKPIs(0.0, 0, 0.0, 0.0, 0.0, None, None)

        def retailer_bonus_kpis(self, retailer=None, start_date=None, end_date=None):
            return RetailerBonusKPIs(0.0, 0.0, 0.0, 0.0, 0.0)

        def spending_by_day(self, retailer=None, start_date=None, end_date=None):
            return []

        def spending_by_month(self, retailer=None, start_date=None, end_date=None):
            return []

        def spending_by_year(self, retailer=None, start_date=None, end_date=None):
            return []

        def weekday_analysis(self, retailer=None, start_date=None, end_date=None):
            return []

        def top_items_by_quantity(self, retailer=None, start_date=None, end_date=None, limit=20):
            return []

        def top_items_by_spend(self, retailer=None, start_date=None, end_date=None, limit=20):
            return []

    state = build_dashboard_state(
        EmptyProvider(),
        retailer=None,
        start_date=None,
        end_date=None,
        time_granularity="Täglich",
        spending_view="Absolut",
        top_view="Menge",
        top_limit=20,
    )
    page = build_dashboard_page_model(state).to_dict()

    assert page["error"] == {"error_code": 102, "detail": "no_receipts"}
    assert page["sections"] == []
