"""Tests for shared KPI DTOs."""

from shared.kpi_dtos import TimeSeriesRow


def test_time_series_row_retailers_default():
    row = TimeSeriesRow(period="2024-01", total_spent=10.0, receipt_count=1)
    assert row.retailers == []


def test_time_series_row_retailers_set():
    row = TimeSeriesRow(
        period="2024-01", total_spent=10.0, receipt_count=1,
        retailers=["lidl", "rewe"],
    )
    assert row.retailers == ["lidl", "rewe"]
