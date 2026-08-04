"""Shared local-file import path for retailer workflows.

This is the single shared orchestration used by both retailer workflows:
load -> parse -> validate -> persist -> skipped-report. Retailer-specific
variation is supplied as plain parameters (loader callable + config values)
instead of subclass hooks.
"""

from pathlib import Path
from typing import Any, Callable, Sequence

from result_types import WorkflowSummary
from reporting.shared_reporting import write_skipped_receipts_report
from shared.receipt_dto import receipt_dict_to_dto
from shared.receipt_store import ReceiptStore

from .error_mapping import render_exception_reason
from .pipeline_runner import parse_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult


def identity_loader(source_path: Path) -> Any:
    """Default loader: pass the source path through as the raw payload."""
    return source_path


def import_local_sources(
    source_paths: Sequence[Path],
    source_dir: Path,
    retailer: str,
    receipts_file: str,
    store: ReceiptStore,
    *,
    loader: Callable[[Path], Any] = identity_loader,
    detail_key: str = "receipt_id",
    load_error_reason_kind: str | None = None,
    retailer_display_name: str = "",
    skipped_report_filename: str = "",
    checked_pages: int | None = None,
    progress_listener: Callable[[object], None] | None = None,
) -> WorkflowResult:
    """Parse, validate and persist a set of local receipt source files."""
    active_source_paths = list(source_paths)

    if not active_source_paths:
        return _build_empty_result(retailer, receipts_file, checked_pages)

    raw_records: list[RawReceiptRecord] = []
    load_issues: list[ReceiptIssue] = []

    for source_path in active_source_paths:
        source_id = source_path.name
        try:
            payload = loader(source_path)
            raw_records.append(RawReceiptRecord(source_id=source_id, payload=payload))
        except Exception as exc:
            load_issues.append(
                ReceiptIssue(
                    source_id=source_id,
                    reason=render_exception_reason(exc, load_error_reason_kind),
                    detail_key=detail_key,
                )
            )

    parse_result = parse_receipts(
        raw_records,
        retailer=retailer,
        detail_key=detail_key,
        progress_listener=progress_listener,
    )
    validation_result = validate_receipts(
        parse_result.records,
        retailer=retailer,
        detail_key=detail_key,
        progress_listener=progress_listener,
    )
    receipt_dtos = [receipt_dict_to_dto(record, retailer) for record in validation_result.records]
    persist_result = store.persist_receipts(receipt_dtos, retailer=retailer)

    skipped_issues = [*load_issues, *parse_result.issues, *validation_result.issues]
    skipped_details = [issue.as_detail() for issue in skipped_issues]
    skipped_report_path = _write_skipped_report(
        source_dir, skipped_details, retailer_display_name, skipped_report_filename
    )
    _print_skipped_receipts(skipped_details, skipped_report_path, retailer_display_name, detail_key)

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


def _write_skipped_report(
    source_dir: Path,
    skipped_details: list[dict[str, str]],
    retailer_display_name: str,
    skipped_report_filename: str,
) -> Path | None:
    """Persist skipped receipts metadata and return the report path."""
    if not skipped_report_filename:
        return None
    report_path = source_dir.parent / skipped_report_filename
    return write_skipped_receipts_report(skipped_details, report_path)


def _print_skipped_receipts(
    skipped_details: list[dict[str, str]],
    report_path: Path | None,
    retailer_display_name: str,
    detail_key: str,
) -> None:
    """Print skipped receipts to stdout/stderr."""
    if not skipped_details:
        return
    prefix = "\u2713" if retailer_display_name == "LIDL" else "\u2139"
    print(f"{prefix} Übersprungene {retailer_display_name}-Bons:")
    for skipped in skipped_details:
        source_id = skipped.get(detail_key) or skipped.get("file") or "unbekannt"
        print(f"  - {source_id}: {skipped['reason']}")
    if report_path:
        print(f"{prefix} Skip-Report geschrieben: {report_path}")


def _build_empty_result(retailer: str, receipts_file: str, checked_pages: int | None) -> WorkflowResult:
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
