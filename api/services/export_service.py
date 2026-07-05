"""Service functions for export endpoints."""

from __future__ import annotations

from typing import Any, Optional

from api.services.kpi_service import get_bonus, get_summary
from storage.sqlite_receipt_store import SqliteReceiptStore


def export_receipts(retailer: Optional[str] = None) -> dict[str, Any]:
    receipts = SqliteReceiptStore.list_receipts(retailer=retailer or "")
    return {"data": receipts}


def export_kpis(retailer: Optional[str] = None) -> dict[str, Any]:
    return {
        "summary": get_summary(retailer=retailer).model_dump(),
        "bonus": get_bonus(retailer=retailer).model_dump(),
    }
