"""Neutral public result/data types shared across workflow-adjacent modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PersistResult:
    """Result of a persistence operation for normalized receipt records."""

    created_count: int
    updated_count: int
    total_receipts: int

    @property
    def processed_count(self) -> int:
        return self.created_count + self.updated_count



@dataclass(frozen=True)
class WorkflowSummary:
    """Normalized workflow summary data used by reporting and orchestration."""

    retailer: str
    processed_count: int
    skipped_count: int
    total_receipts: int
    receipts_file: str
    total_items: int = 0
    checked_pages: int | None = None
    processed_pages: int | None = None


@dataclass(frozen=True)
class ReceiptParseResult:
    """Structured parser result with optional receipt data and skip reason."""

    receipt_data: Optional[Dict[str, Any]]
    skip_reason: Optional[str] = None


