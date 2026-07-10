"""Service functions for receipt endpoints."""

from __future__ import annotations

from math import ceil
from typing import Any, Optional

from storage.sqlite_receipt_store import SqliteReceiptStore


def list_receipts(
    retailer: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    receipts = SqliteReceiptStore.list_receipts(retailer=retailer or "")
    total = len(receipts)
    page_total = max(1, ceil(total / page_size)) if total else 0
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": receipts[start:end],
        "meta": {
            "total": total,
            "page_total": page_total,
            "page": page,
            "page_size": page_size,
        },
    }


def get_receipt(receipt_id: str, retailer: Optional[str] = None) -> dict[str, Any]:
    receipts = SqliteReceiptStore.list_receipts(retailer=retailer or "")
    for receipt in receipts:
        if str(receipt.get("id")) == receipt_id:
            return {"data": receipt}
    raise KeyError(receipt_id)


def get_receipt_items(receipt_id: str, retailer: Optional[str] = None) -> dict[str, Any]:
    receipt = get_receipt(receipt_id, retailer=retailer)["data"]
    return {"data": receipt.get("items", [])}


def get_receipt_payments(receipt_id: str, retailer: Optional[str] = None) -> dict[str, Any]:
    receipt = get_receipt(receipt_id, retailer=retailer)["data"]
    return {"data": receipt.get("payment_methods", [])}


def list_receipts_by_item(
    name: str,
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    return SqliteReceiptStore.list_receipts_by_item(
        name=name,
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
    )


def list_receipts_by_date_range(
    start_date: str,
    end_date: str,
    retailer: Optional[str] = None,
) -> list[dict[str, Any]]:
    return SqliteReceiptStore.list_receipts_by_date_range(
        start_date=start_date,
        end_date=end_date,
        retailer=retailer,
    )
