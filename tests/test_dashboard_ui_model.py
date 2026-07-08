from datetime import date

from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


def test_build_dashboard_page_model_maps_state_to_ui_sections():
    from frontend.ui_model import build_dashboard_page_model
    from frontend.dashboard_state import DashboardDerivedMetrics, DashboardState

    state = DashboardState(
        retailer="lidl",
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
        derived=DashboardDerivedMetrics(122.0, 10.0, 12.0, 12.0, 22.0, 22.0, 4.0, 5.0),
        time_series=[TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)],
        weekday=[WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)],
        top_items=[TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")],
        top_items_total=0,
        min_date=date(2024, 1, 1),
        max_date=date(2024, 1, 31),
    )

    page = build_dashboard_page_model(state)

    assert page.title == "Shopping Analyzer Dashboard"
    assert page.sections[0].kind == "metrics"
    metrics = page.sections[0].items[0]
    assert metrics["spendings"] == 100.0
    assert metrics["spendings_without_discount"] == 122.0
    assert metrics["receipt_count"] == 4
    assert metrics["avg_receipt_amount"] == 25.0
    assert metrics["saved_deposit"] == 2.0
    assert metrics["total_savings"] == 22.0
    assert metrics["total_savings_pct"] == 22.0
    assert metrics["lidlplus_discount_amount"] == 4.0
    assert metrics["sticker_discount_amount"] == 5.0
    assert metrics["lidl_discount_amount"] == 10.0
    assert "rewe_discount_amount" not in metrics
    assert page.sections[1].title == "Ausgaben über Zeit"
    assert page.sections[3].title == "Top-Artikel"


def test_dashboard_page_model_roundtrip_serializer():
    from frontend.ui_model import DashboardPageModel, DashboardSection

    page = DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=[
            DashboardSection(
                kind="metrics",
                title="Kennzahlen",
                items=[{"layout": "single", "cards": [{"title": "A", "items": [{"label": "A", "value": "1"}]}]}],
            ),
            DashboardSection(kind="chart", title="Ausgaben über Zeit", items=[{"period": "2024-01", "total_spent": 10.0}]),
        ],
    )

    payload = page.to_dict()
    restored = DashboardPageModel.from_dict(payload)

    assert payload == {
        "title": "Shopping Analyzer Dashboard",
        "sections": [
            {"kind": "metrics", "title": "Kennzahlen", "items": [{"layout": "single", "cards": [{"title": "A", "items": [{"label": "A", "value": "1"}]}]}]},
            {"kind": "chart", "title": "Ausgaben über Zeit", "items": [{"period": "2024-01", "total_spent": 10.0}]},
        ],
    }
    assert restored == page


def test_dashboard_page_model_json_roundtrip_serializer():
    from frontend.ui_model import DashboardPageModel, DashboardSection

    page = DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=[
            DashboardSection(
                kind="metrics",
                title="Kennzahlen",
                items=[{"layout": "single", "cards": [{"title": "A", "items": [{"label": "A", "value": "1"}]}]}],
            )
        ],
    )

    payload = page.to_json()
    restored = DashboardPageModel.from_json(payload)

    assert '"title": "Shopping Analyzer Dashboard"' in payload
    assert restored == page
