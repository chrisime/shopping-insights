from metrics import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


def test_build_dashboard_state_computes_derived_metrics():
    from frontend.dashboard_state import build_dashboard_state

    calls = []

    class FakeProvider:
        def basic_kpis(self, retailer=None, start_date=None, end_date=None):
            calls.append(("basic", retailer, start_date, end_date))
            return BasicKPIs(
                total_spent=100.0,
                total_receipts=4,
                avg_receipt=25.0,
                total_discount=10.0,
                total_saved_deposit=2.0,
                min_date="2024-01-01",
                max_date="2024-01-31",
            )

        def retailer_bonus_kpis(self, retailer=None, start_date=None, end_date=None):
            calls.append(("bonus", retailer, start_date, end_date))
            return RetailerBonusKPIs(
                rewe_bonus_collected=1.0,
                rewe_bonus_balance=2.0,
                rewe_bonus_redeemed=3.0,
                lidlplus_discount=4.0,
                sticker_discount=5.0,
            )

        def spending_by_month(self, retailer=None, start_date=None, end_date=None):
            calls.append(("trend", retailer, start_date, end_date))
            return [TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)]

        def spending_by_day(self, retailer=None, start_date=None, end_date=None):
            calls.append(("trend_day", retailer, start_date, end_date))
            return [TimeSeriesRow(period="2024-01-01", total_spent=10.0, receipt_count=1)]

        def spending_by_year(self, retailer=None, start_date=None, end_date=None):
            calls.append(("trend_year", retailer, start_date, end_date))
            return [TimeSeriesRow(period="2024", total_spent=10.0, receipt_count=1)]

        def weekday_analysis(self, retailer=None, start_date=None, end_date=None):
            calls.append(("weekday", retailer, start_date, end_date))
            return [WeekdayRow(weekday=0, weekday_name="Montag", trip_count=1, avg_spent=10.0, total_spent=10.0)]

        def top_items_by_quantity(self, retailer=None, start_date=None, end_date=None, limit=20):
            calls.append(("top", retailer, start_date, end_date, limit))
            return [TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")]

        def top_items_by_spend(self, retailer=None, start_date=None, end_date=None, limit=20):
            calls.append(("top_spend", retailer, start_date, end_date, limit))
            return [TopItemRow(name="Apfel", total_quantity=2.0, total_spent=4.0, purchase_count=1, unit="pc")]

    state = build_dashboard_state(
        FakeProvider(),
        retailer="lidl",
        start_date="2024-01-01",
        end_date="2024-01-31",
        time_granularity="Monatlich",
        spending_view="Kumulativ",
        top_view="Menge",
        top_limit=10,
    )

    assert state.kpis.total_spent == 100.0
    assert state.derived.total_before_discount == 122.0
    assert state.derived.total_savings_pct == 22.0
    assert state.time_series[0].total_spent == 10.0
    assert state.weekday[0].weekday_name == "Montag"
    assert state.top_items[0].name == "Apfel"
    assert calls == [
        ("basic", "lidl", None, None),
        ("basic", "lidl", "2024-01-01", "2024-01-31"),
        ("bonus", "lidl", "2024-01-01", "2024-01-31"),
        ("trend", "lidl", "2024-01-01", "2024-01-31"),
        ("weekday", "lidl", "2024-01-01", "2024-01-31"),
        ("top", "lidl", "2024-01-01", "2024-01-31", 10),
    ]
