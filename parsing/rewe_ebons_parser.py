"""Parse REWE eBon PDFs into the same high-level JSON shape used for LIDL.

REWE eBons are delivered as PDFs rather than HTML. This module extracts the
visible text via ``pdfplumber`` and normalizes the most relevant receipt
information into a dict compatible with the existing JSON storage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pdfplumber

from shared.receipt_schema import build_receipt_schema
from .rewe_info_extractor import (
	extract_rewe_receipt_info,
	extract_bonus_amounts_from_text,
	extract_payment_methods_from_lines,
)
from .rewe_items_extractor import extract_rewe_receipt_items
from .rewe_parser_common import to_rewe_float


def parse_rewe_receipt_pdf(pdf_path: str | Path) -> Dict[str, Any]:
	"""Parse a REWE eBon PDF into the normalized receipt structure."""
	path = Path(pdf_path)

	with pdfplumber.open(path) as pdf:
		text = "\n".join((page.extract_text() or "") for page in pdf.pages)

	lines = [line.strip() for line in text.splitlines() if line.strip()]
	if not lines:
		raise ValueError("PDF enthält keinen lesbaren Text")

	return _build_receipt_data(path, text, lines)


def _build_receipt_data(path: Path, text: str, lines: List[str]) -> Dict[str, Any]:
	metadata = extract_rewe_receipt_info(text, lines)
	receipt_id = metadata.get("id")
	purchase_date = metadata.get("purchase_date")
	if not isinstance(receipt_id, str) or not isinstance(purchase_date, str):
		raise ValueError("Bon konnte nicht eindeutig identifiziert werden")

	items_result = extract_rewe_receipt_items(lines)
	rewe_bonus_amount, rewe_total_bonus_amount = extract_bonus_amounts_from_text(text)
	payment_methods, rewe_bonus_saved_amount = extract_payment_methods_from_lines(lines)

	items = items_result.items

	total_price = _calculate_total_price(metadata.get("total_price"), rewe_bonus_saved_amount)
	discount = round(items_result.saved_amount, 2) if items_result.saved_amount > 0 else None
	saved_deposit = round(items_result.saved_deposit, 2) if items_result.saved_deposit > 0 else None
	rewe_bonus_discount = round(rewe_bonus_saved_amount, 2) if rewe_bonus_saved_amount >= 0 else 0.0

	return build_receipt_schema(
		receipt_id=receipt_id,
		retailer="rewe",
		purchase_date=purchase_date,
		store=metadata.get("store"),
		address=metadata.get("address"),
		total_price=total_price,
		discount=discount,
		saved_deposit=saved_deposit,
		rewe_bonus_amount=rewe_bonus_amount,
		rewe_bonus_discount=rewe_bonus_discount,
		rewe_bonus_total_amount=rewe_total_bonus_amount,
		market=metadata.get("market"),
		register=metadata.get("register"),
		cashier=metadata.get("cashier"),
		source_file=path.name,
		payment_methods=payment_methods,
		items=items,
	)


def _calculate_total_price(raw_total_price: object, rewe_bonus_saved_amount: float) -> float | None:
	"""Calculate the final total price after applying rewe bonus deductions."""
	if raw_total_price is None:
		return None
	total = to_rewe_float(raw_total_price)
	if total is None:
		return None
	return round(max(total - rewe_bonus_saved_amount, 0.0), 2)
