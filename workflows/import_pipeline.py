"""Shared local-file import pipeline for retailer workflows."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, Sequence

from result_types import WorkflowSummary
from shared.receipt_store import ReceiptStore

from .error_mapping import render_exception_reason
from .pipeline_runner import parse_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult


class ImportPipeline(ABC):
    """Base class for importing local receipt source files into the DB."""

    detail_key = "file"
    load_error_reason_kind: str | None = None

    def run(
        self,
        source_paths: Sequence[Path],
        source_dir: Path,
        retailer: str,
        receipts_file: str,
        store: ReceiptStore,
        checked_pages: Optional[int] = None,
    ) -> WorkflowResult:
        """Parse, validate and persist a set of local receipt source files."""
        active_source_paths = list(source_paths)

        if not active_source_paths:
            return self._build_empty_result(retailer, receipts_file, checked_pages)

        raw_records: list[RawReceiptRecord] = []
        load_issues: list[ReceiptIssue] = []

        for source_path in active_source_paths:
            source_id = source_path.name
            try:
                payload = self.load_payload(source_path)
                raw_records.append(RawReceiptRecord(source_id=source_id, payload=payload))
            except Exception as exc:
                load_issues.append(
                    ReceiptIssue(
                        source_id=source_id,
                        reason=render_exception_reason(exc, self.load_error_reason_kind),
                        detail_key=self.detail_key,
                    )
                )

        parse_result = parse_receipts(raw_records, retailer=retailer, detail_key=self.detail_key)
        validation_result = validate_receipts(parse_result.records, retailer=retailer, detail_key=self.detail_key)
        persist_result = store.persist_receipts(validation_result.records, retailer=retailer)

        skipped_issues = [*load_issues, *parse_result.issues, *validation_result.issues]
        skipped_details = [issue.as_detail() for issue in skipped_issues]
        skipped_report_path = self.write_skipped_receipts_report(source_dir, skipped_details)
        self.print_skipped_receipts(skipped_details, skipped_report_path)

        return WorkflowResult(
            success=True,
            summary=WorkflowSummary(
                retailer=retailer,
                processed_count=persist_result.processed_count,
                skipped_count=len(skipped_issues),
                total_receipts=persist_result.total_receipts,
                receipts_file=receipts_file,
                total_items=validation_result.total_items,
                checked_pages=checked_pages,
            ),
            skipped_issues=skipped_issues,
            skipped_report_path=skipped_report_path,
        )

    def load_payload(self, source_path: Path) -> Any:
        """Load the raw payload for one local source file."""
        return source_path

    @abstractmethod
    def write_skipped_receipts_report(self, source_dir: Path, skipped_details: list[dict[str, str]]) -> Path | None:
        """Persist skipped receipts metadata and return the report path."""

    @abstractmethod
    def print_skipped_receipts(self, skipped_details: list[dict[str, str]], report_path: Path | None) -> None:
        """Print skipped receipts to stdout/stderr."""

    @staticmethod
    def _build_empty_result(retailer: str, receipts_file: str, checked_pages: Optional[int]) -> WorkflowResult:
        return WorkflowResult(
            success=True,
            summary=WorkflowSummary(
                retailer=retailer,
                processed_count=0,
                skipped_count=0,
                total_receipts=0,
                receipts_file=receipts_file,
                total_items=0,
                checked_pages=checked_pages,
            ),
            skipped_issues=[],
            skipped_report_path=None,
        )

