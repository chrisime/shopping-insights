"""Extract payment method data from Lidl HTML receipts."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from shared.float_parser import parse_german_float
from shared.payment_methods import normalize_payment_method_entry

from .lidl_html_utils import extract_money_from_repeated_id, extract_text_from_repeated_id


def extract_lidl_payment_methods(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract and normalize payment methods from a Lidl receipt."""
    payment_methods: List[Dict[str, Any]] = []

    summary_method = _extract_lidl_summary_tender_description(soup)
    summary_amount = extract_money_from_repeated_id(soup, "purchase_summary_3")

    tender_method_line = extract_text_from_repeated_id(soup, "purchase_tender_information_3")
    tender_amount = extract_money_from_repeated_id(soup, "purchase_tender_information_5")
    card_masked = extract_text_from_repeated_id(soup, "purchase_tender_information_9")
    tender_details = extract_text_from_repeated_id(soup, "purchase_tender_information_10")

    if summary_method or tender_method_line:
        network = None
        if tender_method_line:
            network = tender_method_line.replace("Bezahlung", "").strip() or None

        payment_method = {
            "method": summary_method or network or tender_method_line,
            "amount": summary_amount or tender_amount,
        }
        if network:
            payment_method["network"] = network
        if card_masked:
            payment_method["card_masked"] = card_masked.replace("Kartennr.", "").strip()
        if tender_details:
            payment_method["details"] = tender_details.strip()
        payment_methods.append(payment_method)

    return normalize_lidl_payment_methods(payment_methods)


def normalize_lidl_payment_methods(payment_methods: list[dict]) -> list[dict]:
    """Normalize stored Lidl payment method entries to the canonical schema."""
    normalized_methods: list[dict] = []

    for payment_method in payment_methods or []:
        if not isinstance(payment_method, dict):
            continue

        normalized_method = normalize_payment_method_entry(
            {
                "method": payment_method.get("method"),
                "network": payment_method.get("network"),
                "retailer": "lidl",
                "amount": _extract_numeric_payment_amount(payment_method.get("amount")),
            }
        )
        if normalized_method:
            normalized_methods.append(normalized_method)

    return normalized_methods


def _extract_lidl_summary_tender_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract the tender description from the Lidl purchase summary line."""
    description_spans = soup.find_all(attrs={"data-tender-description": True})
    for span in description_spans:
        text = span.get_text().strip()
        if not text:
            continue
        if re.search(r"\d+,\d{2}", text):
            continue
        return text
    return None


def _normalize_payment_value(value: object) -> Optional[str]:
    """Normalize free-text payment metadata and discard empty placeholders."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        normalized = str(value).strip()
    else:
        normalized = re.sub(r"\s+", " ", str(value)).strip()
    if not normalized or normalized == ":":
        return None
    return normalized


def _extract_numeric_payment_amount(value: object) -> Optional[float]:
    """Normalize payment amounts to floats when a numeric amount is present."""
    normalized = _normalize_payment_value(value)
    if not normalized:
        return None
    return parse_german_float(normalized)
