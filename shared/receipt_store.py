"""Neutrale Port-Schnittstellen zwischen Workflows und Adaptern."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, Sequence

from result_types import PersistResult


@dataclass(frozen=True)
class ReceiptStoreState:
    """Persistierter Delta-Zustand eines Receipts für inkrementelle Abgleiche."""

    source_hash: str | None = None
    payload_hash: str | None = None


class ReceiptStore(Protocol):
    """Persistenzvertrag für normalisierte Receipt-Datensätze."""


    def find_existing_ids(
        self,
        retailer: str,
        file_path: Optional[str] = None,
    ) -> set[str]:
        """Return the already persisted receipt ids used for incremental updates."""

    def find_receipt_states(
        self,
        retailer: str,
        file_path: Optional[str] = None,
    ) -> dict[str, ReceiptStoreState]:
        """Return persisted receipt hashes keyed by receipt id for delta detection."""

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> PersistResult:
        """Persist normalized receipt records and return created/updated/total counts."""

