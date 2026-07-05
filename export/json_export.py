"""JSON export adapter that materializes receipts from SQLite into JSON files."""


from __future__ import annotations

from pathlib import Path

import simplejson

from storage.sqlite_receipt_store import SqliteReceiptStore


def export_receipts_from_db(retailer: str, output_file: str) -> int:
    """Export one retailer's persisted SQLite receipts to JSON."""
    normalized_retailer = retailer.strip().lower()
    if not normalized_retailer:
        raise ValueError("Haendlercode fuer JSON-Export fehlt")

    sqlite_store = SqliteReceiptStore()
    receipts = sqlite_store.list_receipts(retailer=normalized_retailer)
    target_path = Path(output_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("w", encoding="utf-8") as file:
        simplejson.dump(receipts, file, ensure_ascii=False, indent=2)

    return len(receipts)

