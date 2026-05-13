"""Retailer-specific parse and validation dispatch for shared workflow stages."""

from __future__ import annotations

from parsing.lidl_receipt_parser import parse_lidl_ticket
from parsing.lidl_validator import LidlReceiptValidationError, validate_lidl_receipt_data
from parsing.rewe_pdf_parser import parse_rewe_receipt_pdf
from parsing.rewe_validator import ReweReceiptValidationError, validate_rewe_receipt_data

from .pipeline_types import RawReceiptRecord
from .workflow_constants import RETAILER_LIDL, RETAILER_REWE


def parse_raw_record_for_retailer(raw_record: RawReceiptRecord, retailer: str) -> dict:
    """Parse one raw record for the given retailer."""
    if retailer == RETAILER_LIDL:
        return parse_lidl_ticket(raw_record.payload, raw_record.source_id)
    if retailer == RETAILER_REWE:
        return parse_rewe_receipt_pdf(raw_record.payload)
    raise ValueError(f"Unbekannter Händler für Parse-Pipeline: {retailer}")


def validate_receipt_for_retailer(receipt_data: dict, retailer: str) -> None:
    """Validate one parsed receipt for the given retailer."""
    if retailer == RETAILER_LIDL:
        validate_lidl_receipt_data(receipt_data)
        return
    if retailer == RETAILER_REWE:
        validate_rewe_receipt_data(receipt_data)
        return
    raise ValueError(f"Unbekannter Händler für Validierungs-Pipeline: {retailer}")


def validation_error_types_for_retailer(retailer: str) -> tuple[type[Exception], ...]:
    """Return the retailer-specific validation exception types."""
    if retailer == RETAILER_LIDL:
        return (LidlReceiptValidationError,)
    if retailer == RETAILER_REWE:
        return (ReweReceiptValidationError,)
    raise ValueError(f"Unbekannter Händler für Validierungsfehler: {retailer}")

