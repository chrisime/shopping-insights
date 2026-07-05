"""Validation helpers for parsed Lidl receipts."""

from __future__ import annotations

from typing import List

from shared.receipt_schema import ReceiptData
from shared.validation import (
    ReceiptValidationError,
    ValidationIssue,
    validate_common_receipt_fields,
)

from .lidl_pos_extractor import infer_lidl_pos_metadata_from_receipt_id


class LidlReceiptValidationError(ReceiptValidationError):
    retailer_label = "Lidl-Bon"


_LIDL_POS_FIELD_PATTERNS = {
    "market": (r"\d{4}", "ist nicht vierstellig numerisch", "4 Ziffern"),
    "register": (
        r"\d{2,3}",
        "ist nicht zwei- bis dreistellig numerisch",
        "2-3 Ziffern",
    ),
    "cashier": (
        r"\d{5,6}",
        "ist nicht fünf- bis sechsstellig numerisch",
        "5-6 Ziffern",
    ),
    "bon_number": (
        r"\d{5,6}",
        "ist nicht fünf- bis sechsstellig numerisch",
        "5-6 Ziffern",
    ),
}


def validate_lidl_receipt_data(receipt_data: ReceiptData) -> None:
    """Validate a parsed Lidl receipt and raise when the format looks broken."""
    issues: List[ValidationIssue] = []

    validate_common_receipt_fields(
        receipt_data, issues, pos_field_patterns=_LIDL_POS_FIELD_PATTERNS
    )

    inferred_metadata = infer_lidl_pos_metadata_from_receipt_id(
        str(receipt_data.get("id") or receipt_data.get("url") or ""),
    )
    if inferred_metadata:
        for field, inferred_value in inferred_metadata.items():
            current_value = str(receipt_data.get(field) or "").strip()
            if not current_value:
                issues.append(
                    ValidationIssue(
                        field=field,
                        reason="fehlt, obwohl es aus der Receipt-ID ableitbar ist",
                        expected=inferred_value,
                        actual="leer",
                    )
                )
            elif current_value != inferred_value:
                issues.append(
                    ValidationIssue(
                        field=field,
                        reason="passt nicht zur Receipt-ID",
                        expected=inferred_value,
                        actual=current_value,
                    )
                )

    if issues:
        raise LidlReceiptValidationError(issues)
