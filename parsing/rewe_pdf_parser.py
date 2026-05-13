"""Parse REWE eBon PDFs into the same high-level JSON shape used for LIDL.

REWE eBons are delivered as PDFs rather than HTML. This module extracts the
visible text via ``pdfplumber`` and normalizes the most relevant receipt
information into a dict compatible with the existing JSON storage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pdfplumber

from config import get_receipt_schema_profile
from shared.receipt_schema import build_receipt_schema
from .rewe_info_extractor import (
	extract_rewe_receipt_info,
	extract_bonus_amounts_from_text,
	extract_payment_methods_from_lines,
)
from .rewe_items_extractor import extract_rewe_receipt_items
from .rewe_totals_extractor import extract_rewe_totals


def extract_text_from_pdf(pdf_path: Path) -> str:
	"""Extract plain text from all pages of a REWE PDF."""
	with pdfplumber.open(pdf_path) as pdf:
		return "\n".join((page.extract_text() or "") for page in pdf.pages)


def extract_rewe_receipt_metadata_from_pdf(pdf_path: str | Path) -> Dict[str, Any]:
	"""Extract only the lightweight REWE receipt metadata required for update filtering."""
	path = Path(pdf_path)
	text = extract_text_from_pdf(path)

	lines = [line.strip() for line in text.splitlines() if line.strip()]
	if not lines:
		raise ValueError("PDF enthält keinen lesbaren Text")

	return extract_rewe_receipt_info(text, lines)

def parse_rewe_receipt_pdf(pdf_path: str | Path) -> Dict[str, Any]:
	"""Parse a REWE eBon PDF into the normalized receipt structure."""
	path = Path(pdf_path)
	text = extract_text_from_pdf(path)

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
	totals_result = extract_rewe_totals(
		raw_total_price=metadata.get("total_price"),
		saved_amount=items_result.saved_amount,
		saved_deposit=items_result.saved_deposit,
		rewe_bonus_saved_amount=rewe_bonus_saved_amount,
	)
	resolved_rewe_bonus_saved_amount = totals_result.additional_savings.get(
		"rewe_bonus_amount_saved",
		0.0,
	)

	return build_receipt_schema(
		receipt_id=receipt_id,
		retailer="rewe",
		purchase_date=purchase_date,
		store=metadata.get("store"),
		profile=get_receipt_schema_profile("rewe"),
		address=metadata.get("address"),
		total_price=totals_result.total_price,
		amount_saved=totals_result.amount_saved,
		saved_deposit=totals_result.saved_deposit,
		rewe_bonus_amount=rewe_bonus_amount,
		rewe_bonus_amount_saved=resolved_rewe_bonus_saved_amount,
		rewe_bonus_total_amount=rewe_total_bonus_amount,
		market=metadata.get("market"),
		register=metadata.get("register"),
		cashier=metadata.get("cashier"),
		source_file=path.name,
		payment_methods=payment_methods,
		items=items,
	)

