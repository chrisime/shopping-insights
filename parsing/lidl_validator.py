"""Validation helpers for parsed Lidl receipts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from shared.receipt_dates import is_normalized_purchase_date

from .lidl_info_extractor import infer_lidl_pos_metadata_from_receipt_id


@dataclass(frozen=True)
class LidlValidationIssue:
    """Structured validation problem for a parsed Lidl receipt."""

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


class LidlReceiptValidationError(ValueError):
    """Raised when a parsed Lidl receipt no longer matches the expected format."""

    def __init__(self, issues: List[LidlValidationIssue]):
        self.issues = issues
        super().__init__(self.format_issues())

    def format_issues(self) -> str:
        """Return a readable multi-line message for logs and terminal output."""
        lines = ["Lidl-Bonvalidierung fehlgeschlagen:"]
        for issue in self.issues:
            lines.append(f"- {issue.render()}")
        return "\n".join(lines)


def validate_lidl_receipt_data(receipt_data: Dict[str, Any]) -> None:
    """Validate a parsed Lidl receipt and raise when the format looks broken."""
    issues: List[LidlValidationIssue] = []

    items = receipt_data.get("items") or []
    if not items:
        issues.append(LidlValidationIssue(field="items", reason="keine Artikel erkannt"))

    total_price = _parse_amount_to_cents(receipt_data.get("total_price"))
    if total_price is None:
        issues.append(
            LidlValidationIssue(
                field="total_price",
                reason="fehlt oder ist unlesbar",
                actual=str(receipt_data.get("total_price") or "leer"),
            )
        )

    payment_methods = receipt_data.get("payment_methods") or []
    if total_price not in (None, 0) and not payment_methods:
        issues.append(
            LidlValidationIssue(
                field="payment_methods",
                reason="fehlen trotz positivem Gesamtbetrag",
                expected="mindestens eine Zahlungsmethode bei Gesamtbetrag > 0",
                actual="[]",
            )
        )

    for index, payment_method in enumerate(payment_methods, start=1):
        if not isinstance(payment_method, dict):
            issues.append(
                LidlValidationIssue(
                    field=f"payment_methods[{index}]",
                    reason="ist kein Objekt",
                    actual=type(payment_method).__name__,
                )
            )
            continue
        if not str(payment_method.get("method") or "").strip():
            issues.append(
                LidlValidationIssue(
                    field=f"payment_methods[{index}].method",
                    reason="fehlt oder ist leer",
                )
            )
        if total_price not in (None, 0) and _parse_amount_to_cents(payment_method.get("amount")) is None:
            issues.append(
                LidlValidationIssue(
                    field=f"payment_methods[{index}].amount",
                    reason="ist nicht lesbar",
                    actual=str(payment_method.get("amount") or "leer"),
                )
            )

    _validate_field_pattern(
        receipt_data,
        "market",
        r"\d{4}",
        issues,
        "ist nicht vierstellig numerisch",
        expected="4 Ziffern",
    )
    _validate_field_pattern(
        receipt_data,
        "register",
        r"\d{2,3}",
        issues,
        "ist nicht zwei- bis dreistellig numerisch",
        expected="2-3 Ziffern",
    )
    _validate_field_pattern(
        receipt_data,
        "cashier",
        r"\d{5,6}",
        issues,
        "ist nicht fünf- bis sechsstellig numerisch",
        expected="5-6 Ziffern",
    )

    purchase_date = str(receipt_data.get("purchase_date") or "").strip()
    if not is_normalized_purchase_date(purchase_date):
        issues.append(
            LidlValidationIssue(
                field="purchase_date",
                reason="hat nicht das erwartete Datumsformat",
                expected="yyyy-mm-dd",
                actual=purchase_date or "leer",
            )
        )

    inferred_metadata = infer_lidl_pos_metadata_from_receipt_id(
        str(receipt_data.get("id") or receipt_data.get("url") or ""),
    )
    if inferred_metadata:
        for field, inferred_value in inferred_metadata.items():
            current_value = str(receipt_data.get(field) or "").strip()
            if not current_value:
                issues.append(
                    LidlValidationIssue(
                        field=field,
                        reason="fehlt, obwohl es aus der Receipt-ID ableitbar ist",
                        expected=inferred_value,
                        actual="leer",
                    )
                )
            elif current_value != inferred_value:
                issues.append(
                    LidlValidationIssue(
                        field=field,
                        reason="passt nicht zur Receipt-ID",
                        expected=inferred_value,
                        actual=current_value,
                    )
                )

    if issues:
        raise LidlReceiptValidationError(issues)


def _validate_field_pattern(
    receipt_data: Dict[str, Any],
    field_name: str,
    pattern: str,
    issues: List[LidlValidationIssue],
    reason: str,
    expected: str,
) -> None:
    value = str(receipt_data.get(field_name) or "").strip()
    if value and not re.fullmatch(pattern, value):
        issues.append(
            LidlValidationIssue(
                field=field_name,
                reason=reason,
                expected=expected,
                actual=value,
            )
        )


def _parse_amount_to_cents(value: Optional[Any]) -> Optional[int]:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    match = re.search(r"(\d+)(?:[.,](\d{1,2}))?", normalized)
    if not match:
        return None
    euros = int(match.group(1))
    cents = (match.group(2) or "0")[:2].ljust(2, "0")
    return euros * 100 + int(cents)
