"""Storage module for receipt data persistence."""

from shared.receipt_store import ReceiptStore

from .json_receipt_store import JsonReceiptStore, _resolve_receipts_file_path
from .sqlite_receipt_store import SqliteReceiptStore, _resolve_receipts_db_path

WRITE_BACKENDS = ("json", "sqlite")


def resolve_receipt_store_target(
    write_backend: str = "json",
    retailer: str | None = None,
    file_path: str | None = None,
) -> str:
    """Resolve the target file/path for the configured persistence backend."""
    normalized_backend = write_backend.lower()
    if normalized_backend == "json":
        return _resolve_receipts_file_path(file_path=file_path, retailer=retailer)
    if normalized_backend == "sqlite":
        return _resolve_receipts_db_path(file_path=file_path)
    raise ValueError(f"Unbekanntes Write-Backend: {write_backend}")


def create_receipt_store(write_backend: str = "json") -> ReceiptStore:
    """Create the configured receipt store implementation for workflows/entry points."""
    normalized_backend = write_backend.lower()
    if normalized_backend == "json":
        return JsonReceiptStore()
    if normalized_backend == "sqlite":
        return SqliteReceiptStore()
    raise ValueError(f"Unbekanntes Write-Backend: {write_backend}")

__all__ = [
    "ReceiptStore",
    "WRITE_BACKENDS",
    "JsonReceiptStore",
    "SqliteReceiptStore",
    "resolve_receipt_store_target",
    "create_receipt_store",
]
