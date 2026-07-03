"""Parse REWE eBon PDFs into the same high-level JSON shape used for LIDL.

REWE eBons are delivered as PDFs rather than HTML. This module extracts the
visible text via ``pdfplumber`` and normalizes the most relevant receipt
information into a dict compatible with the existing JSON storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pdfplumber

from .receipt_schema import build_receipt_schema
from .rewe_info_extractor import (
    extract_basic_receipt_info_from_text,
    extract_bonus_amounts_from_text,
    extract_payment_methods_from_lines,
)
from .rewe_items_extractor import extract_receipt_items_from_lines
from .rewe_totals_extractor import extract_rewe_totals
from .rewe_validator import ReweReceiptValidationError, validate_rewe_receipt_data


@dataclass(frozen=True)
class RewePdfParseResult:
    """Structured REWE PDF parse result with an optional skip reason."""

    receipt_data: Optional[Dict[str, Any]]
    skip_reason: Optional[str] = None


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract plain text from all pages of a REWE PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def parse_rewe_receipt_pdf(pdf_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Parse a REWE eBon PDF into a normalized receipt dict."""
    return parse_rewe_receipt_pdf_with_diagnostics(pdf_path).receipt_data


def parse_rewe_receipt_pdf_with_diagnostics(
    pdf_path: Union[str, Path]
) -> RewePdfParseResult:
    """Parse a REWE eBon PDF and keep the skip reason for workflow reporting."""
    path = Path(pdf_path)
    try:
        text = extract_text_from_pdf(path)
    except Exception as exc:
        reason = f"PDF konnte nicht gelesen werden: {exc}"
        print(f"✗ REWE-PDF konnte nicht gelesen werden ({path.name}): {exc}")
        return RewePdfParseResult(receipt_data=None, skip_reason=reason)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        print(f"✗ REWE-PDF enthält keinen lesbaren Text: {path.name}")
        return RewePdfParseResult(
            receipt_data=None,
            skip_reason="PDF enthält keinen lesbaren Text",
        )

    receipt_data = _build_receipt_data(path, text, lines)
    if not receipt_data.get("id") or not receipt_data.get("purchase_date"):
        print(f"✗ REWE-PDF konnte nicht eindeutig identifiziert werden: {path.name}")
        return RewePdfParseResult(
            receipt_data=None,
            skip_reason="Bon konnte nicht eindeutig identifiziert werden",
        )

    try:
        validate_rewe_receipt_data(receipt_data)
    except ReweReceiptValidationError as exc:
        print(f"✗ REWE-PDF hat ein unerwartetes Bonformat: {path.name}")
        for line in str(exc).splitlines():
            print(f"  {line}")
        issues_text = "; ".join(issue.render() for issue in exc.issues)
        return RewePdfParseResult(
            receipt_data=None,
            skip_reason=f"Validatorfehler: {issues_text}",
        )

    return RewePdfParseResult(receipt_data=receipt_data)


def _build_receipt_data(path: Path, text: str, lines: List[str]) -> Dict[str, Any]:
    metadata = extract_basic_receipt_info_from_text(text, lines)
    items_result = extract_receipt_items_from_lines(lines)
    rewe_bonus_amount, rewe_total_bonus_amount = extract_bonus_amounts_from_text(text)
    payment_methods, rewe_bonus_saved_amount = extract_payment_methods_from_lines(lines)

    items = items_result.items
    totals_result = extract_rewe_totals(
        raw_total_price=metadata.get("total_price"),
        total_no_saving=items_result.total_no_saving,
        saved_amount=items_result.saved_amount,
        saved_pfand=items_result.saved_pfand,
        rewe_bonus_saved_amount=rewe_bonus_saved_amount,
    )

    return build_receipt_schema(
        receipt_id=metadata["id"],
        retailer="rewe",
        purchase_date=metadata.get("purchase_date"),
        store=metadata.get("store"),
        total_price=totals_result.total_price,
        total_price_no_saving=totals_result.total_price_no_saving,
        amount_saved=totals_result.amount_saved,
        saved_deposit=totals_result.saved_deposit,
        rewe_bonus_amount=rewe_bonus_amount,
        rewe_bonus_amount_saved=totals_result.rewe_bonus_amount_saved,
        rewe_bonus_total_amount=rewe_total_bonus_amount,
        market=metadata.get("market"),
        register=metadata.get("register"),
        cashier=metadata.get("cashier"),
        source_file=path.name,
        payment_methods=payment_methods,
        items=items,
    )


