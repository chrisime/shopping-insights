"""Service functions for export endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from api.services.kpi_service import get_bonus, get_summary
from storage.sqlite_receipt_store import SqliteReceiptStore
from shared.receipt_dates import parse_purchase_date
from shared.retailer_runtime import RETAILERS


def export_receipts(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    receipts = _load_export_receipts(retailer)
    receipts = _filter_receipts_by_purchase_date(receipts, start_date=start_date, end_date=end_date)
    return {"data": receipts}


def export_kpis(retailer: Optional[str] = None) -> dict[str, Any]:
    return {
        "summary": get_summary(retailer=retailer).model_dump(),
        "bonus": get_bonus(retailer=retailer).model_dump(),
    }


def _load_export_receipts(retailer: Optional[str]) -> list[dict[str, Any]]:
    normalized_retailer = str(retailer or "").strip().lower()
    if normalized_retailer:
        return SqliteReceiptStore.list_receipts(retailer=normalized_retailer)

    receipts: list[dict[str, Any]] = []
    for retailer_code in RETAILERS:
        receipts.extend(SqliteReceiptStore.list_receipts(retailer=retailer_code))
    return sorted(receipts, key=_purchase_date_sort_key, reverse=True)


def _filter_receipts_by_purchase_date(
    receipts: list[dict[str, Any]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    start = parse_purchase_date(start_date) if start_date else None
    end = parse_purchase_date(end_date) if end_date else None
    if end is not None:
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    if start is None and end is None:
        return receipts

    filtered: list[dict[str, Any]] = []
    for receipt in receipts:
        purchase_date = parse_purchase_date(receipt.get("purchase_date"))
        if purchase_date is None:
            continue
        if start is not None and purchase_date < start:
            continue
        if end is not None and purchase_date > end:
            continue
        filtered.append(receipt)
    return filtered


def _purchase_date_sort_key(receipt: dict[str, Any]) -> datetime:
    parsed_date = parse_purchase_date(receipt.get("purchase_date"))
    return parsed_date or datetime.min
