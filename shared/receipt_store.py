"""Neutrale Port-Schnittstellen zwischen Workflows und Adaptern."""

from __future__ import annotations

from typing import Protocol, Sequence

from result_types import PersistResult
from shared.receipt_dto import ReceiptDTO

class ReceiptStore(Protocol):
    """Persistenzvertrag für normalisierte Receipt-Datensätze."""


    def find_existing_ids(
        self,
        retailer: str,
    ) -> set[str]:
        """Return the already persisted receipt ids used for incremental updates."""


    def persist_receipts(
        self,
        receipts: Sequence[ReceiptDTO],
        retailer: str,
    ) -> PersistResult:
        """Persist normalized receipt records and return created/updated/total counts."""

