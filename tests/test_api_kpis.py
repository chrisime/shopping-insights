from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


def test_kpi_summary_returns_snake_case_data(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import kpi_service

    captured = {}

    class FakeMetricsStore:
        def basic_kpis(self, retailer=None, start_date=None, end_date=None):
            captured.update(
                retailer=retailer,
                start_date=start_date,
                end_date=end_date,
            )
            return BasicKPIs(
                total_spent=42.5,
                total_receipts=2,
                avg_receipt=21.25,
                total_discount=3.0,
                total_saved_deposit=1.0,
                min_date="2024-01-01",
                max_date="2024-01-31",
            )

    monkeypatch.setattr(kpi_service, "MetricsStore", FakeMetricsStore)

    response = TestClient(app).get(
        "/kpis/summary",
        params={
            "retailer": "lidl",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "total_spent": 42.5,
            "total_receipts": 2,
            "avg_receipt": 21.25,
            "total_discount": 3.0,
            "total_saved_deposit": 1.0,
            "min_date": "2024-01-01",
            "max_date": "2024-01-31",
        }
    }
    assert captured == {
        "retailer": "lidl",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
    }


def test_kpi_bonus_returns_retailer_bonus_data(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import kpi_service

    class FakeMetricsStore:
        def retailer_bonus_kpis(self, retailer=None, start_date=None, end_date=None):
            return RetailerBonusKPIs(
                rewe_bonus_collected=1.5,
                rewe_bonus_balance=2.5,
                rewe_bonus_redeemed=3.5,
                lidlplus_discount=4.5,
                sticker_discount=5.5,
            )

    monkeypatch.setattr(kpi_service, "MetricsStore", FakeMetricsStore)

    response = TestClient(app).get("/kpis/bonus")

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "rewe_bonus_collected": 1.5,
            "rewe_bonus_balance": 2.5,
            "rewe_bonus_redeemed": 3.5,
            "lidlplus_discount": 4.5,
            "sticker_discount": 5.5,
        }
    }


def test_kpi_trend_uses_requested_granularity(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import kpi_service

    called = []

    class FakeMetricsStore:
        def spending_by_month(self, retailer=None, start_date=None, end_date=None):
            called.append("month")
            return [TimeSeriesRow(period="2024-01", total_spent=99.0, receipt_count=4)]

    monkeypatch.setattr(kpi_service, "MetricsStore", FakeMetricsStore)

    response = TestClient(app).get("/kpis/trend", params={"granularity": "month"})

    assert response.status_code == 200
    assert response.json() == {
        "data": [{"period": "2024-01", "total_spent": 99.0, "receipt_count": 4}]
    }
    assert called == ["month"]


def test_kpi_top_items_uses_requested_sort(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import kpi_service

    called = []

    class FakeMetricsStore:
        def top_items_by_spend(self, retailer=None, start_date=None, end_date=None, limit=20):
            called.append(("spend", limit))
            return [
                TopItemRow(
                    name="Apfel",
                    total_quantity=2.0,
                    total_spent=3.0,
                    purchase_count=1,
                    unit="pc",
                )
            ]

    monkeypatch.setattr(kpi_service, "MetricsStore", FakeMetricsStore)

    response = TestClient(app).get("/kpis/top-items", params={"sort": "spend", "limit": 5})

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "name": "Apfel",
                "total_quantity": 2.0,
                "total_spent": 3.0,
                "purchase_count": 1,
                "unit": "pc",
            }
        ]
    }
    assert called == [("spend", 5)]


def test_kpi_weekday_returns_weekday_rows(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import kpi_service

    class FakeMetricsStore:
        def weekday_analysis(self, retailer=None, start_date=None, end_date=None):
            return [
                WeekdayRow(
                    weekday=0,
                    weekday_name="Montag",
                    trip_count=2,
                    avg_spent=12.5,
                    total_spent=25.0,
                )
            ]

    monkeypatch.setattr(kpi_service, "MetricsStore", FakeMetricsStore)

    response = TestClient(app).get("/kpis/weekday")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {
                "weekday": 0,
                "weekday_name": "Montag",
                "trip_count": 2,
                "avg_spent": 12.5,
                "total_spent": 25.0,
            }
        ]
    }
