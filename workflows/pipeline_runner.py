"""Linear shared workflow stages for parsing, validation and persistence."""

from typing import Any, Callable, Optional, Sequence, TypeVar

from parsing.lidl_receipt_parser import parse_lidl_ticket
from parsing.lidl_validator import (
    LidlReceiptValidationError,
    validate_lidl_receipt_data,
)
from parsing.rewe_ebons_parser import parse_rewe_ticket
from parsing.rewe_validator import (
    ReweReceiptValidationError,
    validate_rewe_receipt_data,
)

from .error_mapping import render_exception_reason, render_validation_reason
from .pipeline_types import (
    ParsedReceiptRecord,
    RawReceiptRecord,
    ReceiptIssue,
    StageResult,
)
from .progress_display import ProgressState, ReceiptProgressDisplay
from .workflow_constants import RETAILER_LIDL, RETAILER_REWE

T = TypeVar("T")


def _lookup(table: dict[str, T], retailer: str, label: str) -> T:
    try:
        return table[retailer]
    except KeyError:
        raise ValueError(f"Unbekannter Händler für {label}: {retailer}")


_PARSERS: dict[str, Callable[..., Any]] = {
    RETAILER_LIDL: parse_lidl_ticket,
    RETAILER_REWE: parse_rewe_ticket,
}

_VALIDATORS: dict[str, Callable[..., None]] = {
    RETAILER_LIDL: validate_lidl_receipt_data,
    RETAILER_REWE: validate_rewe_receipt_data,
}

_VALIDATION_ERROR_TYPES: dict[str, tuple[type[Exception], ...]] = {
    RETAILER_LIDL: (LidlReceiptValidationError,),
    RETAILER_REWE: (ReweReceiptValidationError,),
}


def parse_raw_record_for_retailer(raw_record: RawReceiptRecord, retailer: str) -> dict:
    """Parse one raw record for the given retailer."""
    parser = _lookup(_PARSERS, retailer, "Parse-Pipeline")
    return parser(raw_record.payload)


def validate_receipt_for_retailer(receipt_data: dict, retailer: str) -> None:
    """Validate one parsed receipt for the given retailer."""
    validator = _lookup(_VALIDATORS, retailer, "Validierungs-Pipeline")
    validator(receipt_data)


def validation_error_types_for_retailer(retailer: str) -> tuple[type[Exception], ...]:
    """Return the retailer-specific validation exception types."""
    return _lookup(_VALIDATION_ERROR_TYPES, retailer, "Validierungsfehler")


def parse_receipts(
    raw_records: Sequence[RawReceiptRecord],
    retailer: str,
    detail_key: str = "receipt_id",
    unexpected_error_kind: Optional[str] = None,
    progress_listener: Callable[["ProgressState"], None] | None = None,
) -> StageResult[ParsedReceiptRecord]:
    """Parse raw retailer payloads into normalized receipt records."""
    progress = ReceiptProgressDisplay(added_label="Geparst", listener=progress_listener)
    parsed_records: list[ParsedReceiptRecord] = []
    issues: list[ReceiptIssue] = []
    total_records = len(raw_records)
    parsed_items_count = 0

    progress.render_step(0, total_records, 0, 0, 0, "-")

    for index, raw_record in enumerate(raw_records, 1):
        progress.render_step(
            index - 1,
            total_records,
            len(parsed_records),
            len(issues),
            parsed_items_count,
            raw_record.source_id,
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

        progress.render_step(
            index,
            total_records,
            len(parsed_records),
            len(issues),
            parsed_items_count,
            raw_record.source_id,
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
    progress_listener: Callable[["ProgressState"], None] | None = None,
) -> StageResult[dict]:
    """Validate parsed receipt records before persistence."""
    progress = ReceiptProgressDisplay(added_label="Validiert", listener=progress_listener)
    valid_receipts: list[dict] = []
    issues: list[ReceiptIssue] = []
    total_records = len(parsed_records)
    valid_items_count = 0

    progress.render_step(0, total_records, 0, 0, 0, "-")
    validation_error_types = validation_error_types_for_retailer(retailer)

    for index, parsed_record in enumerate(parsed_records, 1):
        progress.render_step(
            index - 1,
            total_records,
            len(valid_receipts),
            len(issues),
            valid_items_count,
            parsed_record.source_id,
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

        progress.render_step(
            index,
            total_records,
            len(valid_receipts),
            len(issues),
            valid_items_count,
            parsed_record.source_id,
        )

    progress.close()
    return StageResult(
        records=valid_receipts,
        issues=issues,
        total_items=valid_items_count,
    )


def _count_total_items(receipts: Sequence[dict]) -> int:
    """Return the total number of items across normalized receipt payloads."""
    return sum(len(receipt.get("items", [])) for receipt in receipts)
