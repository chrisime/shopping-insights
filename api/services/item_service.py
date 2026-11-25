"""Service functions for item endpoints."""

from __future__ import annotations

from typing import Any

from api.schemas.common import paginate_rows
from storage.sqlite_receipt_store import SqliteReceiptStore


def list_items(
    retailer: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    receipts = SqliteReceiptStore.list_receipts(retailer=retailer or "")
    search_value = search.lower().strip() if search else None
    items: list[dict[str, Any]] = []
    for receipt in receipts:
        receipt_id = str(receipt.get("id"))
        for item in receipt.get("items", []):
            name = str(item.get("name", ""))
            if search_value and search_value not in name.lower():
                continue
            items.append(
                {
                    "receipt_id": receipt_id,
                    "name": name,
                    "quantity": item.get("quantity"),
                    "unit": item.get("unit"),
                    "price": item.get("price"),
                }
            )

    return paginate_rows(items, page, page_size)
