"""JSON export adapter that materializes receipts from SQLite into JSON files."""


from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import simplejson

from shared.retailer_runtime import get_retailer_runtime
from storage.sqlite_receipt_store import SqliteReceiptStore


def resolve_receipts_export_path(output_file: Optional[str] = None, retailer: str = "") -> str:
    """Resolve the JSON output path for one retailer export."""
    if output_file:
        return output_file

    if not retailer:
        raise ValueError("Haendler fuer JSON-Export erforderlich")

    retailer_runtime = get_retailer_runtime(retailer)
    if retailer_runtime is None:
        raise ValueError(f"Unbekannter Haendler fuer JSON-Export: {retailer}")
    return retailer_runtime.receipts_json_file


def export_receipts_from_db(retailer: str, output_file: Optional[str] = None) -> int:
    """Export one retailer's persisted SQLite receipts to JSON."""
    normalized_retailer = str(retailer or "").strip().lower()
    if not normalized_retailer:
        raise ValueError("Haendlercode fuer JSON-Export fehlt")

    sqlite_store = SqliteReceiptStore()
    receipts = sqlite_store.list_receipts(retailer=normalized_retailer)
    target_file = resolve_receipts_export_path(output_file=output_file, retailer=normalized_retailer)
    _write_json_receipts(receipts=receipts, output_file=target_file)
    return len(receipts)


def _write_json_receipts(receipts: list[dict[str, Any]], output_file: str) -> None:
    """Write exported receipts as formatted UTF-8 JSON."""
    target_path = Path(output_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as file:
        simplejson.dump(receipts, file, ensure_ascii=False, indent=2)
