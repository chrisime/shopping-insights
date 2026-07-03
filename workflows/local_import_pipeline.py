"""Shared local-file import pipeline for retailer workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from result_types import WorkflowSummary
from shared.receipt_store import ReceiptStore

from .error_mapping import render_exception_reason
from .pipeline_runner import parse_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult

PayloadLoader = Callable[[Path], Any]
SkippedReportWriter = Callable[[Path, list[dict[str, str]]], Path]
SkippedPrinter = Callable[[list[dict[str, str]], Path | None], None]


def run_local_import_pipeline(
    *,
    source_paths: Sequence[Path],
    source_dir: Path,
    retailer: str,
    receipts_file: str,
    store: ReceiptStore,
    load_payload: PayloadLoader,
    write_skipped_receipts_report: SkippedReportWriter,
    print_skipped_receipts: SkippedPrinter,
    detail_key: str = "file",
    load_error_reason_kind: str | None = None,
    prefilter_issues: Optional[Sequence[ReceiptIssue]] = None,
    existing_total_receipts: Optional[int] = None,
    checked_pages: Optional[int] = None,
) -> WorkflowResult:
    """Parse, validate and persist a set of local receipt source files."""
    active_source_paths = list(source_paths)
    initial_issues = list(prefilter_issues or [])

    if not active_source_paths:
        return _build_empty_result(
            source_dir=source_dir,
            retailer=retailer,
            receipts_file=receipts_file,
            initial_issues=initial_issues,
            existing_total_receipts=existing_total_receipts,
            checked_pages=checked_pages,
            write_skipped_receipts_report=write_skipped_receipts_report,
            print_skipped_receipts=print_skipped_receipts,
        )

    raw_records: list[RawReceiptRecord] = []
    load_issues: list[ReceiptIssue] = []

    for source_path in active_source_paths:
        source_id = source_path.name
        try:
            payload = load_payload(source_path)
            raw_records.append(RawReceiptRecord(source_id=source_id, payload=payload))
        except Exception as exc:
            load_issues.append(
                ReceiptIssue(
                    source_id=source_id,
                    reason=render_exception_reason(exc, load_error_reason_kind),
                    detail_key=detail_key,
                )
            )

    parse_result = parse_receipts(raw_records, retailer=retailer, detail_key=detail_key)
    validation_result = validate_receipts(parse_result.records, retailer=retailer, detail_key=detail_key)
    receipts_to_persist = validation_result.records
    persist_result = store.persist_receipts(receipts_to_persist, retailer=retailer)

    skipped_issues = [*initial_issues, *load_issues, *parse_result.issues, *validation_result.issues]
    skipped_details = [issue.as_detail() for issue in skipped_issues]
    skipped_report_path = write_skipped_receipts_report(source_dir, skipped_details)
    print_skipped_receipts(skipped_details, skipped_report_path)

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


def _build_empty_result(
    *,
    source_dir: Path,
    retailer: str,
    receipts_file: str,
    initial_issues: Sequence[ReceiptIssue],
    existing_total_receipts: Optional[int],
    checked_pages: Optional[int],
    write_skipped_receipts_report: SkippedReportWriter,
    print_skipped_receipts: SkippedPrinter,
) -> WorkflowResult:
    skipped_details = [issue.as_detail() for issue in initial_issues]
    skipped_report_path = None
    if skipped_details:
        skipped_report_path = write_skipped_receipts_report(source_dir, skipped_details)
        print_skipped_receipts(skipped_details, skipped_report_path)

    return WorkflowResult(
        success=True,
        summary=WorkflowSummary(
            retailer=retailer,
            processed_count=0,
            skipped_count=len(initial_issues),
            total_receipts=existing_total_receipts or 0,
            receipts_file=receipts_file,
            total_items=0,
            checked_pages=checked_pages,
        ),
        skipped_issues=list(initial_issues),
        skipped_report_path=skipped_report_path,
    )

