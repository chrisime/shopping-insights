"""Storage module for receipt persistence (DB-first)."""
from shared.receipt_store import ReceiptStore

from .receipt_repository import add_receipt_to_json, sort_receipts_by_date, upsert_receipts
from .sqlite_receipt_store import SqliteReceiptStore


def create_receipt_store() -> ReceiptStore:
    """Create the default DB-backed receipt store implementation."""
    return SqliteReceiptStore()

__all__ = [
    "add_receipt_to_json",
    "ReceiptStore",
    "SqliteReceiptStore",
    "create_receipt_store",
    "sort_receipts_by_date",
    "upsert_receipts",
]
