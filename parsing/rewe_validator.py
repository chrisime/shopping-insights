"""Validation helpers for parsed REWE receipts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from shared.receipt_dates import is_normalized_purchase_date, normalize_purchase_date_from_receipt_id_token


REWE_ID_RE = re.compile(
	r"^rewe-(?P<market>\d+)-(?P<register>\d+)-(?P<date>\d{8})-(?P<time>\d{4})-(?P<bon>\d+)$"
)


@dataclass(frozen=True)
class ReweValidationIssue:
	"""Structured validation problem for a parsed REWE receipt."""

	field: str
	reason: str
	expected: Optional[str] = None
	actual: Optional[str] = None

	def render(self) -> str:
		head = f"{self.field}: {self.reason}"
		details = []
		if self.expected:
			details.append(f"erwartet={self.expected}")
		if self.actual:
			details.append(f"bekommen={self.actual}")
		if details:
			return f"{head} ({', '.join(details)})"
		return head


class ReweReceiptValidationError(ValueError):
	"""Raised when a parsed REWE receipt no longer matches the expected format."""

	def __init__(self, issues: List[ReweValidationIssue]):
		self.issues = issues
		super().__init__(self.format_issues())

	def format_issues(self) -> str:
		lines = ["REWE-Bonvalidierung fehlgeschlagen:"]
		for issue in self.issues:
			lines.append(f"- {issue.render()}")
		return "\n".join(lines)


def validate_rewe_receipt_data(receipt_data: Dict[str, Any]) -> None:
	"""Validate a parsed REWE receipt and raise when the format looks broken."""
	issues: List[ReweValidationIssue] = []

	retailer = str(receipt_data.get("retailer") or "").strip().lower()
	if retailer and retailer != "rewe":
		issues.append(
			ReweValidationIssue(
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
			ReweValidationIssue(
				field="id",
				reason="hat nicht das erwartete REWE-ID-Format",
				expected="rewe-<markt>-<kasse>-<ddmmyyyy>-<hhmm>-<bon>",
				actual=receipt_id or "leer",
			)
		)

	purchase_date = str(receipt_data.get("purchase_date") or "").strip()
	if not is_normalized_purchase_date(purchase_date):
		issues.append(
			ReweValidationIssue(
				field="purchase_date",
				reason="hat nicht das erwartete Datumsformat",
				expected="yyyy-mm-dd",
				actual=purchase_date or "leer",
			)
		)

	items = receipt_data.get("items") or []
	if not items:
		issues.append(ReweValidationIssue(field="items", reason="keine Artikel erkannt"))

	total_price = _parse_amount_to_cents(receipt_data.get("total_price"))
	if total_price is None:
		issues.append(
			ReweValidationIssue(
				field="total_price",
				reason="fehlt oder ist unlesbar",
				actual=str(receipt_data.get("total_price") or "leer"),
			)
		)

	payment_methods = receipt_data.get("payment_methods") or []
	if total_price not in (None, 0) and not payment_methods:
		issues.append(
			ReweValidationIssue(
				field="payment_methods",
				reason="fehlen trotz positivem Gesamtbetrag",
				expected="mindestens eine Zahlungsmethode bei Gesamtbetrag > 0",
				actual="[]",
			)
		)

	for index, payment_method in enumerate(payment_methods, start=1):
		if not isinstance(payment_method, dict):
			issues.append(
				ReweValidationIssue(
					field=f"payment_methods[{index}]",
					reason="ist kein Objekt",
					actual=type(payment_method).__name__,
				)
			)
			continue
		if not str(payment_method.get("method") or "").strip():
			issues.append(
				ReweValidationIssue(
					field=f"payment_methods[{index}].method",
					reason="fehlt oder ist leer",
				)
			)
		if total_price not in (None, 0) and _parse_amount_to_cents(payment_method.get("amount")) is None:
			issues.append(
				ReweValidationIssue(
					field=f"payment_methods[{index}].amount",
					reason="ist nicht lesbar",
					actual=str(payment_method.get("amount") or "leer"),
				)
			)

	_validate_field_pattern(
		receipt_data,
		"market",
		r"\d{3,4}",
		issues,
		reason="ist nicht drei- bis vierstellig numerisch",
		expected="3-4 Ziffern",
	)
	_validate_field_pattern(
		receipt_data,
		"register",
		r"\d{1,3}",
		issues,
		reason="ist nicht ein- bis dreistellig numerisch",
		expected="1-3 Ziffern",
	)
	_validate_field_pattern(
		receipt_data,
		"cashier",
		r"\d{4,6}",
		issues,
		reason="ist nicht vier- bis sechsstellig numerisch",
		expected="4-6 Ziffern",
	)

	if id_match:
		_validate_id_consistency(receipt_data, id_match, issues)

	if issues:
		raise ReweReceiptValidationError(issues)


def _validate_id_consistency(
	receipt_data: Dict[str, Any],
	id_match: re.Match[str],
	issues: List[ReweValidationIssue],
) -> None:
	expected_market = id_match.group("market")
	expected_register = id_match.group("register")
	expected_date = id_match.group("date")
	expected_purchase_date = normalize_purchase_date_from_receipt_id_token(expected_date)

	market = str(receipt_data.get("market") or "").strip()
	if market and market != expected_market:
		issues.append(
			ReweValidationIssue(
				field="market",
				reason="passt nicht zur Receipt-ID",
				expected=expected_market,
				actual=market,
			)
		)

	register = str(receipt_data.get("register") or "").strip()
	if register and register != expected_register:
		issues.append(
			ReweValidationIssue(
				field="register",
				reason="passt nicht zur Receipt-ID",
				expected=expected_register,
				actual=register,
			)
		)

	purchase_date = str(receipt_data.get("purchase_date") or "").strip()
	if purchase_date and expected_purchase_date:
		if purchase_date != expected_purchase_date:
			issues.append(
				ReweValidationIssue(
					field="purchase_date",
					reason="Datum passt nicht zur Receipt-ID",
					expected=expected_purchase_date,
					actual=purchase_date,
				)
			)


def _validate_field_pattern(
	receipt_data: Dict[str, Any],
	field_name: str,
	pattern: str,
	issues: List[ReweValidationIssue],
	reason: str,
	expected: str,
) -> None:
	value = str(receipt_data.get(field_name) or "").strip()
	if value and not re.fullmatch(pattern, value):
		issues.append(
			ReweValidationIssue(
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

