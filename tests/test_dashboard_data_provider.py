from metrics import BasicKPIs


def test_api_dashboard_provider_basic_kpis_parses_json():
    from frontend.data_provider import ApiDashboardDataProvider

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeSession:
        def get(self, url, params=None, timeout=None):
            assert url == "https://example.test/kpis/summary"
            assert params == {"retailer": "lidl", "start_date": "2024-01-01", "end_date": "2024-01-31"}
            return FakeResponse(
                {
                    "data": {
                        "total_spent": 12.5,
                        "total_receipts": 2,
                        "avg_receipt": 6.25,
                        "total_discount": 1.0,
                        "total_saved_deposit": 0.5,
                        "min_date": "2024-01-01",
                        "max_date": "2024-01-31",
                    }
                }
            )

    provider = ApiDashboardDataProvider("https://example.test", session=FakeSession())

    result = provider.basic_kpis(retailer="lidl", start_date="2024-01-01", end_date="2024-01-31")

    assert result == BasicKPIs(
        total_spent=12.5,
        total_receipts=2,
        avg_receipt=6.25,
        total_discount=1.0,
        total_saved_deposit=0.5,
        min_date="2024-01-01",
        max_date="2024-01-31",
    )


def test_api_dashboard_provider_bonus_and_trend_paths():
    from frontend.data_provider import ApiDashboardDataProvider

    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeSession:
        def get(self, url, params=None, timeout=None):
            calls.append((url, params))
            if url.endswith("/kpis/bonus"):
                return FakeResponse(
                    {
                        "data": {
                            "rewe_bonus_collected": 1.0,
                            "rewe_bonus_balance": 2.0,
                            "rewe_bonus_redeemed": 3.0,
                            "lidlplus_discount": 4.0,
                            "sticker_discount": 5.0,
                        }
                    }
                )
            return FakeResponse({"data": [{"period": "2024-01", "total_spent": 9.0, "receipt_count": 1}]})

    provider = ApiDashboardDataProvider("https://example.test", session=FakeSession())

    bonus = provider.retailer_bonus_kpis(retailer="rewe")
    trend = provider.spending_by_month(retailer="lidl", start_date="2024-01-01", end_date="2024-01-31")

    assert bonus.rewe_bonus_collected == 1.0
    assert trend[0].period == "2024-01"
    assert calls == [
        ("https://example.test/kpis/bonus", {"retailer": "rewe"}),
        (
            "https://example.test/kpis/trend",
            {"retailer": "lidl", "start_date": "2024-01-01", "end_date": "2024-01-31", "granularity": "month"},
        ),
    ]


def test_api_dashboard_provider_top_items_and_weekday_paths():
    from frontend.data_provider import ApiDashboardDataProvider

    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class FakeSession:
        def get(self, url, params=None, timeout=None):
            calls.append((url, params))
            if url.endswith("/kpis/top-items"):
                return FakeResponse(
                    {"data": [{"name": "Apfel", "total_quantity": 2.0, "total_spent": 3.0, "purchase_count": 1, "unit": "pc"}]}
                )
            return FakeResponse(
                {"data": [{"weekday": 0, "weekday_name": "Montag", "trip_count": 2, "avg_spent": 12.5, "total_spent": 25.0}]}
            )

    provider = ApiDashboardDataProvider("https://example.test", session=FakeSession())

    items = provider.top_items_by_spend(limit=7)
    weekdays = provider.weekday_analysis(retailer="rewe")

    assert items[0].name == "Apfel"
    assert weekdays[0].weekday_name == "Montag"
    assert calls == [
        ("https://example.test/kpis/top-items", {"sort": "spend", "limit": "7"}),
        ("https://example.test/kpis/weekday", {"retailer": "rewe"}),
    ]


def test_get_dashboard_data_provider_uses_api_base_url(monkeypatch):
    from frontend.data_provider import ApiDashboardDataProvider, get_dashboard_data_provider

    monkeypatch.setenv("API_BASE_URL", "https://example.test")

    provider = get_dashboard_data_provider()

    assert isinstance(provider, ApiDashboardDataProvider)
