"""Storage module for receipt persistence (DB-first)."""
from shared.receipt_store import ReceiptStore

from .sqlite_receipt_store import SqliteReceiptStore


def create_receipt_store() -> ReceiptStore:
    """Create the default DB-backed receipt store implementation."""
    return SqliteReceiptStore()

__all__ = [
    "ReceiptStore",
    "SqliteReceiptStore",
    "create_receipt_store",
]
