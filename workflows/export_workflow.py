"""Workflows for exporting persisted receipts from SQLite into external formats."""

from __future__ import annotations

from typing import Optional

from config import storage_config
from export.json_export import export_receipts_from_db
from shared.retailer_runtime import get_retailer_runtime


def run_export_json_from_db(retailer: str, output_file: Optional[str] = None) -> bool:
    """Export all receipts of one retailer from SQLite into a JSON file."""
    print(f"\n=== EXPORT: {retailer} nach JSON ===")

    normalized_retailer = str(retailer or "").strip().lower()
    target_file = output_file
    if not target_file:
        retailer_runtime = get_retailer_runtime(normalized_retailer)
        if retailer_runtime is None:
            print(f"✗ Unbekannter Händler: {retailer}")
            return False
        target_file = retailer_runtime.receipts_json_file

    print(f"Quelle: SQLite ({storage_config.SQLITE_RECEIPTS_DB_FILE})")
    print(f"Ziel:   {target_file}")

    count = export_receipts_from_db(normalized_retailer, target_file)
    print(f"✓ Export abgeschlossen: {count} Bons geschrieben")
    return True
