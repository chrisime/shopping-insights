"""Extract REWE receipt metadata, bonus amounts and payment methods from PDF text."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from shared.addresses import empty_address

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

    purchase_date = _normalize_rewe_purchase_date(date_value)

    receipt_id_parts = ["rewe"]
    for part in (market, register, date_value, time_value, bon_number):
        if part:
            receipt_id_parts.append(part.replace(".", "").replace(":", ""))

    return {
        "id": "-".join(receipt_id_parts) if len(receipt_id_parts) > 1 else None,
        "purchase_date": purchase_date,
        "total_price": total_price,
        "address": _extract_header_address(lines),
        "market": market,
        "register": register,
        "cashier": cashier,
        "store": _extract_store(lines),
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
        payment_methods.append(
            {
                "method": method,
                "amount": numeric_amount,
            }
        )
        if _is_rewe_bonus_payment_method(method):
            rewe_bonus_saved_amount += numeric_amount
    return payment_methods, rewe_bonus_saved_amount



def _extract_store(lines: List[str]) -> str:
    footer_store = _extract_footer_store(lines)
    if footer_store:
        return footer_store

    header_lines: List[str] = []
    for line in lines:
        if line == "EUR" or line.startswith("UID Nr"):
            break
        header_lines.append(line)

    for line in header_lines:
        company = _extract_company_from_line(line)
        if company:
            return company

    return header_lines[0] if header_lines else "REWE"


def _extract_header_address(lines: List[str]) -> dict:
    """Extract the structured store address from the receipt header block."""
    header_lines: List[str] = []
    for line in lines:
        if line == "EUR" or line.startswith("UID Nr"):
            break
        header_lines.append(line)

    return extract_address_from_lines(header_lines) or empty_address()


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



def _is_rewe_bonus_payment_method(method: str) -> bool:
    normalized_method = method.strip().lower()
    return "bonus" in normalized_method and "guthaben" in normalized_method


def _normalize_rewe_purchase_date(date_value: Optional[str]) -> Optional[str]:
    """Convert REWE dates from dd.mm.yyyy to yyyy.mm.dd."""
    if not date_value:
        return None
    day, month, year = date_value.split(".")
    return f"{year}.{month}.{day}"

