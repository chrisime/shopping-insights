from datetime import date

from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


def test_time_series_items_include_retailers():
    from api.services.dashboard_service import DashboardDerivedMetrics, DashboardState
    from api.services.dashboard_service import build_dashboard_page_model

    state = DashboardState(
        retailer=None,
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_granularity="Monatlich",
        spending_view="Absolut",
        top_view="Menge",
        top_limit=10,
        search=None,
        page=1,
        available_kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        kpis=BasicKPIs(100.0, 4, 25.0, 10.0, 2.0, "2024-01-01", "2024-01-31"),
        bonus_kpis=RetailerBonusKPIs(1.0, 2.0, 3.0, 4.0, 5.0),
        derived=DashboardDerivedMetrics(117.0, 10.0, 9.0, 9.0, 19.0, 19.0, 4.0, 5.0),
        time_series=[
            TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1, retailers=["lidl"]),
            TimeSeriesRow(period="2024-02", total_spent=20.0, receipt_count=2, retailers=["rewe"]),
        ],
        weekday=[WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)],
        top_items=[TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")],
        top_items_total=0,
        min_date=date(2024, 1, 1),
        max_date=date(2024, 1, 31),
    )

    page = build_dashboard_page_model(state).to_dict()
    time_series_section = next(s for s in page["sections"] if s["kind"] == "time_series")

    for item in time_series_section["items"]:
        assert "retailers" in item
        assert isinstance(item["retailers"], list)

    assert time_series_section["items"][0]["retailers"] == ["lidl"]
    assert time_series_section["items"][1]["retailers"] == ["rewe"]
