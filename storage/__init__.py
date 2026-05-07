"""Storage module for receipt data persistence."""

from shared.ports import ReceiptStore

from .json_receipt_store import (
    JsonReceiptStore,
    sort_receipts_by_date,
    upsert_receipts,
)

WRITE_BACKENDS = ("json",)


def create_receipt_store(write_backend: str = "json") -> ReceiptStore:
    """Create the configured receipt store implementation for workflows/entry points."""
    normalized_backend = write_backend.lower()
    if normalized_backend == "json":
        return JsonReceiptStore()
    raise ValueError(f"Unbekanntes Write-Backend: {write_backend}")

__all__ = [
    "ReceiptStore",
    "WRITE_BACKENDS",
    "JsonReceiptStore",
    "create_receipt_store",
    "sort_receipts_by_date",
    "upsert_receipts",
]
