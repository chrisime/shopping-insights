"""Shared validation infrastructure for parsed receipt data.

Provides the base classes and helpers used by retailer-specific validators
to avoid structural duplication.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from shared.float_parser import parse_amount_to_cents
from shared.receipt_dates import is_normalized_purchase_date
from shared.receipt_schema import ReceiptData


@dataclass(frozen=True)
class ValidationIssue:
    """Structured validation problem for a parsed receipt."""

    field: str
    reason: str
    expected: Optional[str] = None
    actual: Optional[str] = None

    def render(self) -> str:
        """Render the issue as a compact, user-facing bullet line."""
        head = f"{self.field}: {self.reason}"
        details = []
        if self.expected:
            details.append(f"erwartet={self.expected}")
        if self.actual:
            details.append(f"bekommen={self.actual}")
        if details:
            return f"{head} ({', '.join(details)})"
        return head


class ReceiptValidationError(ValueError):
    """Raised when a parsed receipt no longer matches the expected format."""

    retailer_label: str = "Bon"

    def __init__(self, issues: List[ValidationIssue]):
        self.issues = issues
        super().__init__(self.format_issues())

    def format_issues(self) -> str:
        lines = [f"{self.retailer_label}-Validierung fehlgeschlagen:"]
        for issue in self.issues:
            lines.append(f"- {issue.render()}")
        return "\n".join(lines)


def validate_field_pattern(
    receipt_data: ReceiptData,
    field_name: str,
    pattern: str,
    issues: List[ValidationIssue],
    reason: str,
    expected: str,
) -> None:
    """Validate a single text field against a regex pattern.

    Appends a ``ValidationIssue`` when the field is non-empty but does not
    match the given pattern.
    """
    value = str(receipt_data.get(field_name) or "").strip()
    if value and not re.fullmatch(pattern, value):
        issues.append(
            ValidationIssue(
                field=field_name,
                reason=reason,
                expected=expected,
                actual=value,
            )
        )


def validate_payment_methods(
    receipt_data: ReceiptData,
    issues: List[ValidationIssue],
) -> None:
    """Validate ``payment_methods`` presence, structure, and amounts.

    Appends issues for:
    - Missing payment methods when total > 0
    - Non-dict method entries
    - Missing or empty ``method`` values
    - Unparseable ``amount`` values
    """
    total_price = parse_amount_to_cents(receipt_data.get("total_price"))
    payment_methods = receipt_data.get("payment_methods") or []

    if total_price not in (None, 0) and not payment_methods:
        issues.append(
            ValidationIssue(
                field="payment_methods",
                reason="fehlen trotz positivem Gesamtbetrag",
                expected="mindestens eine Zahlungsmethode bei Gesamtbetrag > 0",
                actual="[]",
            )
        )

    for index, payment_method in enumerate(payment_methods, start=1):
        if not isinstance(payment_method, dict):
            issues.append(
                ValidationIssue(
                    field=f"payment_methods[{index}]",
                    reason="ist kein Objekt",
                    actual=type(payment_method).__name__,
                )
            )
            continue
        if not str(payment_method.get("method") or "").strip():
            issues.append(
                ValidationIssue(
                    field=f"payment_methods[{index}].method",
                    reason="fehlt oder ist leer",
                )
            )
        if (
            total_price not in (None, 0)
            and parse_amount_to_cents(payment_method.get("amount")) is None
        ):
            issues.append(
                ValidationIssue(
                    field=f"payment_methods[{index}].amount",
                    reason="ist nicht lesbar",
                    actual=str(payment_method.get("amount") or "leer"),
                )
            )


def validate_common_receipt_fields(
    receipt_data: ReceiptData,
    issues: List[ValidationIssue],
    pos_field_patterns: Optional[Dict[str, tuple[str, str, str]]] = None,
) -> None:
    """Validate fields common to all retailer receipts.

    Checks items presence, total_price, payment methods, purchase_date,
    and POS field patterns when provided.
    """
    items = receipt_data.get("items") or []
    if not items:
        issues.append(ValidationIssue(field="items", reason="keine Artikel erkannt"))

    total_price = parse_amount_to_cents(receipt_data.get("total_price"))
    if total_price is None:
        issues.append(
            ValidationIssue(
                field="total_price",
                reason="fehlt oder ist unlesbar",
                actual=str(receipt_data.get("total_price") or "leer"),
            )
        )

    validate_payment_methods(receipt_data, issues)

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

    if pos_field_patterns:
        for field_name, (pattern, reason, expected) in pos_field_patterns.items():
            validate_field_pattern(
                receipt_data, field_name, pattern, issues, reason, expected=expected
            )
