"""Validation helpers for parsed REWE receipts."""

from __future__ import annotations

import re
from typing import Dict, List

from shared.receipt_dates import normalize_purchase_date_from_receipt_id_token
from shared.receipt_schema import ReceiptData
from shared.validation import (
    ValidationIssue,
    ReceiptValidationError,
    validate_common_receipt_fields,
)


REWE_ID_RE = re.compile(
    r"^rewe-(?P<market>\d+)-(?P<register>\d+)-(?P<date>\d{8})-(?P<time>\d{4})-(?P<bon>\d+)$"
)


# Backward-compatible aliases
ReweValidationIssue = ValidationIssue


class ReweReceiptValidationError(ReceiptValidationError):
    retailer_label = "REWE-Bon"


_REWE_POS_FIELD_PATTERNS = {
    "market": (r"\d{3,4}", "ist nicht drei- bis vierstellig numerisch", "3-4 Ziffern"),
    "register": (r"\d{1,3}", "ist nicht ein- bis dreistellig numerisch", "1-3 Ziffern"),
    "cashier": (r"\d{4,6}", "ist nicht vier- bis sechsstellig numerisch", "4-6 Ziffern"),
    "bon_number": (r"\d+", "ist nicht numerisch", "mindestens 1 Ziffer"),
}


def validate_rewe_receipt_data(receipt_data: ReceiptData) -> None:
    """Validate a parsed REWE receipt and raise when the format looks broken."""
    issues: List[ValidationIssue] = []

    retailer = str(receipt_data.get("retailer") or "").strip().lower()
    if retailer and retailer != "rewe":
        issues.append(
            ValidationIssue(
                field="retailer",
                reason="ist nicht rewe",
                expected="rewe",
                actual=retailer,
            )
        )

    receipt_id = str(receipt_data.get("id") or "").strip()
    id_match = REWE_ID_RE.fullmatch(receipt_id)
    if not id_match:
        issues.append(
            ValidationIssue(
                field="id",
                reason="hat nicht das erwartete REWE-ID-Format",
                expected="rewe-<markt>-<kasse>-<ddmmyyyy>-<hhmm>-<bon>",
                actual=receipt_id or "leer",
            )
        )

    validate_common_receipt_fields(receipt_data, issues, pos_field_patterns=_REWE_POS_FIELD_PATTERNS)

    if id_match:
        _validate_id_consistency(receipt_data, id_match, issues)

    if issues:
        raise ReweReceiptValidationError(issues)


def _validate_id_consistency(
    receipt_data: Dict[str, str | None],
    id_match: re.Match[str],
    issues: List[ValidationIssue],
) -> None:
    expected_market = id_match.group("market")
    expected_register = id_match.group("register")
    expected_date = id_match.group("date")
    expected_bon_number = id_match.group("bon")
    expected_purchase_date = normalize_purchase_date_from_receipt_id_token(expected_date)

    market = str(receipt_data.get("market") or "").strip()
    if market and market != expected_market:
        issues.append(
            ValidationIssue(
                field="market",
                reason="passt nicht zur Receipt-ID",
                expected=expected_market,
                actual=market,
            )
        )

    register = str(receipt_data.get("register") or "").strip()
    if register and register != expected_register:
        issues.append(
            ValidationIssue(
                field="register",
                reason="passt nicht zur Receipt-ID",
                expected=expected_register,
                actual=register,
            )
        )

    bon_number = str(receipt_data.get("bon_number") or "").strip()
    if bon_number and bon_number != expected_bon_number:
        issues.append(
            ValidationIssue(
                field="bon_number",
                reason="passt nicht zur Receipt-ID",
                expected=expected_bon_number,
                actual=bon_number,
            )
        )

    purchase_date = str(receipt_data.get("purchase_date") or "").strip()
    if purchase_date and expected_purchase_date:
        if purchase_date != expected_purchase_date:
            issues.append(
                ValidationIssue(
                    field="purchase_date",
                    reason="Datum passt nicht zur Receipt-ID",
                    expected=expected_purchase_date,
                    actual=purchase_date,
                )
            )
