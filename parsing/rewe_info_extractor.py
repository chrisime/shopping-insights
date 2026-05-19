"""Extract REWE receipt metadata, bonus amounts and payment methods from PDF text."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from shared.addresses import empty_address
from shared.receipt_dates import normalize_purchase_date
from shared.payment_methods import normalize_payment_method_entry

from .address_extractor import extract_address_from_lines
from .rewe_parser_common import to_rewe_float


SUM_RE = re.compile(r"SUMME EUR\s+(?P<amount>\d+,\d{2})")
DATETIME_AND_BON_RE = re.compile(
    r"(?P<date>\d{2}\.\d{2}\.\d{4})\s+"
    r"(?P<time>\d{2}:\d{2})(?::\d{2})?\s+"
    r"Bon-Nr\.\s*:\s*(?P<bon>\d+)"
)
BON_RE = re.compile(r"Bon-Nr\.\s*:\s*(?P<bon>\d+)")
DATE_RE = re.compile(r"Datum\s*:\s*(?P<date>\d{2}\.\d{2}\.\d{4})")
TIME_RE = re.compile(r"Uhrzeit\s*:\s*(?P<time>\d{2}:\d{2})(?::\d{2})?\s*Uhr")
MARKET_RE = re.compile(
    r"Markt\s*:\s*(?P<market>\d+)\s+"
    r"Kasse\s*:\s*(?P<register>\d+)\s+"
    r"Bed\.\s*:\s*(?P<cashier>\d+)"
)
PAYMENT_RE = re.compile(r"^Geg\.\s+(?P<method>.+?)\s+EUR\s+(?P<amount>-?\d+,\d{2})$")
REWE_BONUS_AMOUNT_RE = re.compile(
    r"Mit diesem Einkauf hast du\s+(?P<amount>\d+,\d{2})\s+EUR\s+"
    r"REWE Bonus-Guthaben gesammelt:",
    re.IGNORECASE,
)
REWE_TOTAL_BONUS_AMOUNT_RE = re.compile(
    r"Aktuelles Bonus-Guthaben:\s*(?P<amount>\d+,\d{2})\s+EUR",
    re.IGNORECASE,
)
REWE_COMPANY_RE = re.compile(
    r"(?P<company>\bREWE(?:[-\s][^,]+?)?\s+(?:oHG|GmbH|KG|AG|eG|e\.K\.?)\b)",
    re.IGNORECASE,
)
FOOTER_START_RE = re.compile(r"^(?:UID\s*Nr\.?|UID-Nr\.?|USt-IdNr\.?|USt\.?-IdNr\.?)", re.IGNORECASE)


def extract_bonus_amounts_from_text(text: str) -> Tuple[float, Optional[float]]:
    """Extract collected and total REWE bonus amounts from the raw PDF text."""
    bonus_match = REWE_BONUS_AMOUNT_RE.search(text)
    total_bonus_match = REWE_TOTAL_BONUS_AMOUNT_RE.search(text)
    return (
        to_rewe_float(bonus_match.group("amount")) if bonus_match else 0.0,
        to_rewe_float(total_bonus_match.group("amount")) if total_bonus_match else None,
    )



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
    total_price = to_rewe_float(total_match.group("amount")) if total_match else None

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
        "store": store,
    }



def extract_payment_methods_from_lines(lines: List[str]) -> Tuple[List[Dict[str, Any]], float]:
    """Extract REWE payment methods and total redeemed bonus amount."""
    payment_methods: List[Dict[str, Any]] = []
    rewe_bonus_saved_amount = 0.0
    for line in lines:
        payment_match = PAYMENT_RE.match(line)
        if not payment_match:
            continue
        method = payment_match.group("method").strip()
        amount = payment_match.group("amount")
        numeric_amount = to_rewe_float(amount)
        normalized_method = normalize_payment_method_entry(
            {
                "method": method,
                "retailer": "rewe",
                "amount": numeric_amount,
            }
        )
        if normalized_method:
            payment_methods.append(normalized_method)
        if _is_rewe_bonus_payment_method(method):
            rewe_bonus_saved_amount += numeric_amount
    return payment_methods, rewe_bonus_saved_amount



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

    if header_lines and extract_address_from_lines([header_lines[0]]) is None:
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
        if line == "EUR" or _is_footer_start_line(line):
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


def _looks_like_metadata_line(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", line or "").strip().lower()
    return any(
        marker in normalized
        for marker in (
            "bon-nr",
            "summe",
            "geg.",
            "markt:",
            "kasse",
            "bed.",
            "uid",
            "ust-idnr",
            "uhrzeit",
            "datum",
            "bonus",
            " eur",
        )
    ) or normalized == "eur"



def _is_rewe_bonus_payment_method(method: str) -> bool:
    normalized_method = method.strip().lower()
    return "bonus" in normalized_method and "guthaben" in normalized_method
