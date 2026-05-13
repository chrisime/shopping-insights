"""Neutrale Port-Schnittstellen zwischen Workflows und Adaptern."""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Sequence

from result_types import PersistResult


class ReceiptStore(Protocol):
    """Persistenzvertrag für normalisierte Receipt-Datensätze."""


    def find_existing_ids(
        self,
        retailer: str,
        file_path: Optional[str] = None,
    ) -> set[str]:
        """Return the already persisted receipt ids used for incremental updates."""

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> PersistResult:
        """Persist normalized receipt records and return created/updated/total counts."""

