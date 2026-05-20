"""Workflows for exporting persisted receipts from SQLite into external formats."""

from __future__ import annotations

from typing import Optional

from config import storage_config
from export.json_export import export_receipts_from_db


def run_export_json_from_db(retailer: str, output_file: Optional[str] = None) -> bool:
    """Export all receipts of one retailer from SQLite into a JSON file."""
    print(f"\n=== EXPORT: {retailer.upper()} nach JSON ===")
    target_label = output_file or "Standarddatei des Händlers"
    print(f"Quelle: SQLite ({storage_config.SQLITE_RECEIPTS_DB_FILE})")
    print(f"Ziel:   {target_label}")

    count = export_receipts_from_db(
        retailer=retailer,
        output_file=output_file,
    )
    print(f"✓ Export abgeschlossen: {count} Bons geschrieben")
    return True

