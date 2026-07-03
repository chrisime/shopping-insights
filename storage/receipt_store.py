"""Persistence interfaces and JSON-backed receipt store implementations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Sequence, Tuple

from .receipt_repository import sort_receipts_by_date, upsert_receipts


class ReceiptStore(Protocol):
    """Persistence contract for normalized receipt records."""

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        """Persist normalized receipt records and return created/updated/total counts."""


class JsonReceiptStore:
    """JSON-backed receipt store used by the current workflows."""

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> Tuple[int, int, int]:
        created_count, updated_count, _ = upsert_receipts(
            receipts,
            file_path=file_path,
            retailer=retailer,
        )
        total_receipts = sort_receipts_by_date(file_path=file_path, retailer=retailer)
        return created_count, updated_count, total_receipts

