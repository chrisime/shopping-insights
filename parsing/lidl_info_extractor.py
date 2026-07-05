"""Extract basic receipt information from HTML content.

Keep store/address resolution, total price extraction, and header line parsing.
Payment methods, POS metadata, and discount extraction have been moved to
dedicated modules for single-responsibility separation.
"""

import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup

from shared.float_parser import parse_german_float
from shared.addresses import empty_address, normalize_address

from .address_extractor import extract_address_from_lines
from .lidl_html_utils import extract_text_from_repeated_id, extract_money_from_repeated_id
from .lidl_payment_extractor import extract_lidl_payment_methods
from .lidl_pos_extractor import apply_lidl_pos_metadata
from .lidl_discount_extractor import apply_lidl_discount_fields, apply_lidl_plus_discount

_LIDL_HEADER_LINES_LIMIT = 8
_LIDL_STORE_NAME = "lidl"

def extract_lidl_receipt_info(
    soup: BeautifulSoup,
    receipt_id: str,
    store: str,
    address: Optional[dict] = None,
) -> Dict[str, Any]:
    """Extract raw receipt metadata from Lidl HTML.

    Returns a dict with resolved store/address plus extracted fields:
    payment_methods, market, register, cashier, bon_number, total_price,
    discount, lidlplus_discount, sticker_discount, sticker_discount_pct.
    Does *not* build the full schema — the caller is responsible for that.
    """
    normalized_api_address = normalize_address(address) if address else empty_address()
    extracted_html_address = _extract_lidl_address_from_html(soup)
    resolved_address = (
        extracted_html_address
        if _has_address_content(extracted_html_address)
        else normalized_api_address
    )

    extracted_store_name = _extract_lidl_store_name_from_html(soup)
    resolved_store_name = (
        extracted_store_name
        if extracted_store_name
        else _resolve_lidl_store_name(
            fallback_store_name=store,
            api_address=normalized_api_address,
            html_address=resolved_address,
        )
    )

    raw: Dict[str, Any] = {
        "store": resolved_store_name,
        "address": resolved_address,
        "payment_methods": [],
        "market": None,
        "register": None,
        "cashier": None,
        "bon_number": None,
        "total_price": None,
        "discount": None,
        "lidlplus_discount": None,
        "sticker_discount": None,
        "sticker_discount_pct": [],
    }

    raw["payment_methods"] = extract_lidl_payment_methods(soup)
    raw = apply_lidl_pos_metadata(raw, soup, receipt_id)
    raw = _apply_lidl_total_price(raw, soup)
    raw = apply_lidl_discount_fields(raw, soup)
    raw = apply_lidl_plus_discount(raw, soup)

    return raw


def _extract_lidl_store_name_from_html(soup: BeautifulSoup) -> Optional[str]:
    """Extract branch name from the first Lidl header line when available."""
    header_lines = _extract_lidl_header_lines(soup, include_fallback=False)
    if len(header_lines) < 3:
        return None

    # Canonical layout: branch name / street+no / zip+city
    if extract_address_from_lines(header_lines[1:3]) is None:
        return None

    store_name = header_lines[0].strip()
    return store_name or None


def _resolve_lidl_store_name(
    fallback_store_name: str,
    api_address: Dict[str, Any],
    html_address: Dict[str, Any],
) -> str:

    resolved_store_name = (fallback_store_name or _LIDL_STORE_NAME).strip() or _LIDL_STORE_NAME
    if resolved_store_name.lower() != _LIDL_STORE_NAME:
        return resolved_store_name

    # If HTML city differs from API city, API city commonly carries the branch suffix.
    api_city = str(api_address.get("city") or "").strip()
    html_city = str(html_address.get("city") or "").strip()
    if api_city and html_city and api_city != html_city:
        return api_city

    return resolved_store_name


def _has_address_content(address: Dict[str, Any]) -> bool:
    return any(address.get(key) not in (None, "") for key in ("street", "street_no", "zip", "city"))


def _extract_lidl_address_from_html(soup: BeautifulSoup) -> dict:
    """Fallback: extract address from visible HTML header lines when API provides none."""
    header_lines = _extract_lidl_header_lines(soup)
    return extract_address_from_lines(header_lines) or empty_address()


def _extract_lidl_header_lines(soup: BeautifulSoup, *, include_fallback: bool = True) -> list[str]:
    """Read header_line_* entries first; fallback to generic stripped text for legacy receipts."""
    header_lines = []
    for index in range(1, _LIDL_HEADER_LINES_LIMIT + 1):
        line = extract_text_from_repeated_id(soup, f"header_line_{index}")
        if line:
            header_lines.append(line)

    if header_lines:
        return header_lines

    if not include_fallback:
        return []

    return list(soup.stripped_strings)[:_LIDL_HEADER_LINES_LIMIT]


def _apply_lidl_total_price(receipt_data: Dict[str, Any], soup: BeautifulSoup) -> Dict[str, Any]:
    """Apply the final amount to pay from Lidl summary or tender lines to the receipt data."""
    try:
        purchase_summary_elements = soup.find_all(id=re.compile(r"^purchase_summary_"))
        for element in purchase_summary_elements:
            element_text = element.get_text().strip().lower()
            if "zu zahlen" not in element_text:
                continue
            parent = element.parent
            amount_spans = parent.find_all("span", class_="css_bold") if parent else []
            for span in amount_spans:
                price = parse_german_float(span.get_text())
                if price is not None:
                    receipt_data["total_price"] = price
                    return receipt_data
    except (AttributeError, TypeError):
        pass

    tender_amount = extract_money_from_repeated_id(soup, "purchase_tender_information_5")
    if tender_amount is not None:
        receipt_data["total_price"] = tender_amount

    return receipt_data



