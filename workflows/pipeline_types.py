"""Shared data types for linear receipt workflow pipelines."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from result_types import WorkflowSummary


@dataclass(frozen=True)
class RawReceiptRecord:
    """Raw fetched receipt payload identified by its source id."""

    source_id: str
    payload: Any


@dataclass(frozen=True)
class ParsedReceiptRecord:
    """Parsed normalized receipt data identified by its source id."""

    source_id: str
    receipt_data: dict[str, Any]


@dataclass(frozen=True)
class ReceiptIssue:
    """Structured workflow issue that can be rendered into reporting details."""

    source_id: str
    reason: str
    detail_key: str = "receipt_id"

    def as_detail(self) -> dict[str, str]:
        return {
            self.detail_key: self.source_id,
            "reason": self.reason,
        }


TRecord = TypeVar("TRecord")


@dataclass(frozen=True)
class StageResult(Generic[TRecord]):
    """Result of a linear workflow stage with records plus structured issues."""

    records: list[TRecord]
    issues: list[ReceiptIssue]
    total_items: int = 0



@dataclass(frozen=True)
class WorkflowResult:
    """Complete result of a retailer workflow run."""

    success: bool
    summary: WorkflowSummary
    skipped_issues: list[ReceiptIssue]
    skipped_report_path: Path | None = None
