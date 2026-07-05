"""Extract REWE receipt metadata (store, address, POS) from PDF text.

Bonus amounts and payment methods have been moved to dedicated modules.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from shared.addresses import empty_address
from shared.metadata_markers import METADATA_MARKERS as _SHARED_METADATA_MARKERS
from shared.receipt_dates import normalize_purchase_date

from shared.float_parser import parse_german_float

from .address_extractor import extract_address_from_lines

SUM_RE = re.compile(r"SUMME EUR\s+(?P<amount>\d+,\d{2})")
DATETIME_AND_BON_RE = re.compile(
    r"(?P<date>\d{1,2}\.\d{1,2}\.\d{4})\s+"
    r"(?P<time>\d{1,2}:\d{2})(?::\d{2})?\s+"
    r"Bon-Nr\.\s*:\s*(?P<bon>\d+)"
)
BON_RE = re.compile(r"Bon-Nr\.\s*:\s*(?P<bon>\d+)")
DATE_RE = re.compile(r"Datum\s*:\s*(?P<date>\d{1,2}\.\d{1,2}\.\d{4})")
TIME_RE = re.compile(r"Uhrzeit\s*:\s*(?P<time>\d{1,2}:\d{2})(?::\d{2})?\s*Uhr")
MARKET_RE = re.compile(
    r"Markt\s*:\s*(?P<market>\d+)\s+"
    r"Kasse\s*:\s*(?P<register>\d+)\s+"
    r"Bed\.\s*:\s*(?P<cashier>\d+)"
)
REWE_COMPANY_RE = re.compile(
    r"(?P<company>\bREWE(?:[-\s][^,]+?)?\s+(?:oHG|GmbH|KG|AG|eG|e\.K\.?)\b)",
    re.IGNORECASE,
)
FOOTER_START_RE = re.compile(r"^(?:UID\s*Nr\.?|UID-Nr\.?|USt-IdNr\.?|USt\.?-IdNr\.?)", re.IGNORECASE)

def extract_rewe_receipt_info(text: str, lines: List[str]) -> Dict[str, Optional[Any]]:
    """Extract REWE metadata such as receipt id, purchase date and POS identifiers."""
    datetime_match = DATETIME_AND_BON_RE.search(text)
    date_value = datetime_match.group("date") if datetime_match else None
    time_value = datetime_match.group("time") if datetime_match else None
    bon_number = datetime_match.group("bon") if datetime_match else None

    if date_value is None:
        date_match = DATE_RE.search(text)
        if date_match:
            date_value = date_match.group("date")

    if time_value is None:
        time_match = TIME_RE.search(text)
        if time_match:
            time_value = time_match.group("time")

    if bon_number is None:
        bon_match = BON_RE.search(text)
        if bon_match:
            bon_number = bon_match.group("bon")

    market_match = MARKET_RE.search(text)
    market = market_match.group("market") if market_match else None
    register = market_match.group("register") if market_match else None
    cashier = market_match.group("cashier") if market_match else None

    total_match = SUM_RE.search(text)
    total_price = parse_german_float(total_match.group("amount")) if total_match else None

    purchase_date = normalize_purchase_date(date_value)
    store = _extract_store(lines)

    receipt_id_parts = ["rewe"]
    for part in (market, register, date_value, time_value, bon_number):
        if part:
            receipt_id_parts.append(part.replace(".", "").replace(":", ""))

    return {
        "id": "-".join(receipt_id_parts) if len(receipt_id_parts) > 1 else None,
        "purchase_date": purchase_date,
        "total_price": total_price,
        "address": _extract_store_address(lines, store),
        "market": market,
        "register": register,
        "cashier": cashier,
        "bon_number": bon_number,
        "store": store,
    }






def _extract_store(lines: List[str]) -> str:
    footer_lines = _extract_footer_lines(lines)
    footer_store = _extract_footer_store(footer_lines)
    if footer_store:
        return footer_store

    header_lines = _extract_header_lines(lines)

    for line in header_lines:
        company = _extract_company_from_line(line)
        if company:
            return company

    if header_lines:
        # Some REWE eBon variants start with a two-line address block and no legal entity name.
        # In that case, do not use the street line as store name.
        if extract_address_from_lines(header_lines[:2]) is not None:
            return "REWE"
        if extract_address_from_lines([header_lines[0]]) is None:
            return header_lines[0]

    return "REWE"


def _extract_store_address(lines: List[str], store: Optional[str]) -> dict:
    """Extract the first valid structured store address from header, footer or fallback lines."""
    header_lines = _extract_header_lines(lines)
    footer_lines = _extract_footer_lines(lines)

    header_address = _find_first_valid_address(header_lines)
    if header_address:
        return header_address

    footer_address = _find_first_valid_address(footer_lines)
    if footer_address:
        return footer_address

    if store:
        fallback_address = _find_first_valid_address([store])
        if fallback_address:
            return fallback_address

    return empty_address()


def _extract_header_lines(lines: List[str]) -> List[str]:
    header_lines: List[str] = []
    for line in lines:
        if line == REWE_BODY_MARKER or _is_footer_start_line(line):
            break
        header_lines.append(line)
    return header_lines


def _extract_footer_lines(lines: List[str]) -> List[str]:
    for index, line in enumerate(lines):
        if _is_footer_start_line(line):
            return lines[index + 1 :]
    return []


def _extract_footer_store(lines: List[str]) -> Optional[str]:
    """Prefer the company/legal-entity line from the footer section of the eBon."""
    for line in reversed(lines):
        company = _extract_company_from_line(line)
        if company:
            return company
    return None


def _extract_company_from_line(line: str) -> Optional[str]:
    """Extract a REWE legal-entity/company name from a single receipt line."""
    normalized = re.sub(r"\s+", " ", line).strip()
    if not normalized:
        return None

    match = REWE_COMPANY_RE.search(normalized)
    if not match:
        return None

    return match.group("company").strip()


def _find_first_valid_address(lines: List[str]) -> Optional[dict]:
    """Return the first address-like block that parses cleanly and is not metadata."""
    for start_index in range(len(lines)):
        for window_size in (1, 2, 3):
            candidate_lines = lines[start_index : start_index + window_size]
            if not candidate_lines:
                continue
            if any(_looks_like_metadata_line(line) for line in candidate_lines):
                continue
            parsed_address = extract_address_from_lines(candidate_lines)
            if not parsed_address:
                continue
            return parsed_address
    return None


def _is_footer_start_line(line: str) -> bool:
    return FOOTER_START_RE.match(line.strip()) is not None


REWE_BODY_MARKER = "EUR"


_REWE_METADATA_MARKERS = (
    "bonus",
    " eur",
)


def _looks_like_metadata_line(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", line or "").strip().lower()
    return (
        any(marker in normalized for marker in _SHARED_METADATA_MARKERS)
        or any(marker in normalized for marker in _REWE_METADATA_MARKERS)
        or normalized == REWE_BODY_MARKER.lower()
    )
