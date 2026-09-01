"""Validation helpers for parsed dm receipts."""

from __future__ import annotations

import re

from shared.receipt_dates import is_normalized_purchase_date
from shared.receipt_schema import ReceiptData
from shared.validation import ValidationIssue, ReceiptValidationError


DM_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_\d{4}$"
)


class DmReceiptValidationError(ReceiptValidationError):
    retailer_label = "dm-Bon"


def validate_dm_receipt_data(receipt_data: ReceiptData) -> None:
    """Validate a parsed dm receipt and raise when the format looks broken.

    dm eBons intentionally carry no payment methods, so the shared payment
    method check is omitted here.
    """
    issues: list[ValidationIssue] = []

    retailer = str(receipt_data.get("retailer") or "").strip().lower()
    if retailer and retailer != "dm":
        issues.append(
            ValidationIssue(
                field="retailer",
                reason="ist nicht dm",
                expected="dm",
                actual=retailer,
            )
        )

    receipt_id = str(receipt_data.get("id") or "").strip()
    if not DM_ID_RE.fullmatch(receipt_id):
        issues.append(
            ValidationIssue(
                field="id",
                reason="hat nicht das erwartete dm-ID-Format",
                expected="<uuid>_<jahr>",
                actual=receipt_id or "leer",
            )
        )

    items = receipt_data.get("items") or []
    if not items:
        issues.append(ValidationIssue(field="items", reason="keine Artikel erkannt"))

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
        raise DmReceiptValidationError(issues)