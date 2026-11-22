"""Validation helpers for parsed Rossmann receipts."""

from __future__ import annotations

import re

from shared.receipt_dates import is_normalized_purchase_date
from shared.receipt_schema import ReceiptData
from shared.validation import ValidationIssue, ReceiptValidationError


ROSSMANN_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class RossmannReceiptValidationError(ReceiptValidationError):
    retailer_label = "Rossmann-Bon"


def validate_rossmann_receipt_data(receipt_data: ReceiptData) -> None:
    """Validate a parsed Rossmann receipt and raise when the format looks broken.

    Rossmann/anybill receipts intentionally may carry no payment methods, so the
    shared payment method check is omitted here.
    """
    issues: list[ValidationIssue] = []

    retailer = str(receipt_data.get("retailer") or "").strip().lower()
    if retailer and retailer != "rossmann":
        issues.append(
            ValidationIssue(
                field="retailer",
                reason="ist nicht rossmann",
                expected="rossmann",
                actual=retailer,
            )
        )

    receipt_id = str(receipt_data.get("id") or "").strip()
    if not ROSSMANN_ID_RE.fullmatch(receipt_id):
        issues.append(
            ValidationIssue(
                field="id",
                reason="hat nicht das erwartete UUID-Format",
                expected="<uuid>",
                actual=receipt_id or "leer",
            )
        )

    if receipt_data.get("total_price") is None:
        issues.append(
            ValidationIssue(
                field="total_price",
                reason="fehlt oder ist unlesbar",
                actual=str(receipt_data.get("total_price") or "leer"),
            )
        )

    purchase_date = str(receipt_data.get("purchase_date") or "").strip()
    if not is_normalized_purchase_date(purchase_date):
        issues.append(
            ValidationIssue(
                field="purchase_date",
                reason="hat nicht das erwartete Datumsformat",
                expected="yyyy-mm-dd",
                actual=purchase_date or "leer",
            )
        )

    if issues:
        raise RossmannReceiptValidationError(issues)