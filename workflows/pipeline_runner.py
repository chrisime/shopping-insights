"""Linear shared workflow stages for parsing, validation and persistence."""

from __future__ import annotations

from typing import Optional, Sequence

from result_types import PersistResult
from shared.receipt_store import ReceiptStore

from .progress_display import ProgressState, ReceiptProgressDisplay
from .retailer_pipeline import (
    parse_raw_record_for_retailer,
    validate_receipt_for_retailer,
    validation_error_types_for_retailer,
)
from .error_mapping import render_exception_reason, render_validation_reason
from .pipeline_types import (
    ParsedReceiptRecord,
    RawReceiptRecord,
    ReceiptIssue,
    StageResult,
)

def parse_receipts(
    raw_records: Sequence[RawReceiptRecord],
    retailer: str,
    detail_key: str = "receipt_id",
    unexpected_error_kind: Optional[str] = None,
) -> StageResult[ParsedReceiptRecord]:
    """Parse raw retailer payloads into normalized receipt records."""
    progress = ReceiptProgressDisplay(added_label="Geparst")
    parsed_records: list[ParsedReceiptRecord] = []
    issues: list[ReceiptIssue] = []
    total_records = len(raw_records)
    parsed_items_count = 0

    progress.render(ProgressState(0, total_records, 0, 0, 0, 0, "-"))

    for index, raw_record in enumerate(raw_records, 1):
        progress.render(
            ProgressState(
                current=index - 1,
                total=total_records,
                added=len(parsed_records),
                skipped=len(issues),
                errors=len(issues),
                items=parsed_items_count,
                current_receipt=raw_record.source_id,
            )
        )

        try:
            receipt_data = parse_raw_record_for_retailer(raw_record, retailer)
            parsed_records.append(
                ParsedReceiptRecord(
                    source_id=raw_record.source_id,
                    receipt_data=receipt_data,
                )
            )
            parsed_items_count += len(receipt_data.get("items", []))
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(
                ReceiptIssue(
                    source_id=raw_record.source_id,
                    reason=render_exception_reason(exc),
                    detail_key=detail_key,
                )
            )
        except Exception as exc:  # pragma: no cover - filesystem/pdfplumber dependent
            issues.append(
                ReceiptIssue(
                    source_id=raw_record.source_id,
                    reason=render_exception_reason(exc, unexpected_error_kind),
                    detail_key=detail_key,
                )
            )

        progress.render(
            ProgressState(
                current=index,
                total=total_records,
                added=len(parsed_records),
                skipped=len(issues),
                errors=len(issues),
                items=parsed_items_count,
                current_receipt=raw_record.source_id,
            )
        )

    progress.close()
    return StageResult(
        records=parsed_records,
        issues=issues,
        total_items=parsed_items_count,
    )


def validate_receipts(
    parsed_records: Sequence[ParsedReceiptRecord],
    retailer: str,
    detail_key: str = "receipt_id",
) -> StageResult[dict]:
    """Validate parsed receipt records before persistence."""
    progress = ReceiptProgressDisplay(added_label="Validiert")
    valid_receipts: list[dict] = []
    issues: list[ReceiptIssue] = []
    total_records = len(parsed_records)
    valid_items_count = 0

    progress.render(ProgressState(0, total_records, 0, 0, 0, 0, "-"))
    validation_error_types = validation_error_types_for_retailer(retailer)

    for index, parsed_record in enumerate(parsed_records, 1):
        progress.render(
            ProgressState(
                current=index - 1,
                total=total_records,
                added=len(valid_receipts),
                skipped=len(issues),
                errors=len(issues),
                items=valid_items_count,
                current_receipt=parsed_record.source_id,
            )
        )

        try:
            validate_receipt_for_retailer(parsed_record.receipt_data, retailer)
            valid_receipts.append(parsed_record.receipt_data)
            valid_items_count += _count_total_items([parsed_record.receipt_data])
        except validation_error_types as exc:
            issues.append(
                ReceiptIssue(
                    source_id=parsed_record.source_id,
                    reason=render_validation_reason(exc),
                    detail_key=detail_key,
                )
            )

        progress.render(
            ProgressState(
                current=index,
                total=total_records,
                added=len(valid_receipts),
                skipped=len(issues),
                errors=len(issues),
                items=valid_items_count,
                current_receipt=parsed_record.source_id,
            )
        )

    progress.close()
    return StageResult(
        records=valid_receipts,
        issues=issues,
        total_items=valid_items_count,
    )


def persist_valid_receipts(
    receipts: Sequence[dict],
    retailer: str,
    store: ReceiptStore,
    file_path: Optional[str] = None,
) -> PersistResult:
    """Persist validated receipts via the configured store implementation."""
    return store.persist_receipts(
        receipts,
        retailer=retailer,
        file_path=file_path,
    )


def _count_total_items(receipts: Sequence[dict]) -> int:
    """Return the total number of items across normalized receipt payloads."""
    return sum(len(receipt.get("items", [])) for receipt in receipts)
