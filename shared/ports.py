"""Neutrale Port-Schnittstellen zwischen Workflows und Adaptern."""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Sequence

from result_types import PersistResult, ReceiptStoreSnapshot


class ReceiptStore(Protocol):
    """Persistenzvertrag für normalisierte Receipt-Datensätze."""

    def load_receipts_snapshot(
        self,
        retailer: str,
        file_path: Optional[str] = None,
    ) -> ReceiptStoreSnapshot:
        """Load existing ids, raw receipts and the resolved target path for a retailer."""

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> PersistResult:
        """Persist normalized receipt records and return created/updated/total counts."""

