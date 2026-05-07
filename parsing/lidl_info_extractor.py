"""Extract basic receipt information from HTML content."""

import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup

from shared.receipt_schema import build_receipt_schema
from shared.addresses import normalize_address

from .address_extractor import extract_address_from_lines


LIDL_POS_LINE_RE = re.compile(
    r"(?P<market>\d{4})\s+(?P<cashier>\d{5,6})/(?P<register>\d{2,3})\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{2})\s+(?P<time>\d{2}:\d{2})"
)
LIDL_SERIAL_LINE_RE = re.compile(r"LDL-\d{3}-(?P<market>\d{4})-(?P<register>\d{2,3})")
LIDL_STORE_NAME = "lidl"


def extract_lidl_receipt_info(
    soup: BeautifulSoup,
    receipt_id: str,
    receipt_date: str,
    store: str,
    address: Optional[dict] = None,
) -> Dict[str, Any]:
    """Extract basic receipt information using the exact logic from the provided code snippet."""
    receipt_data = build_receipt_schema(
        receipt_id=receipt_id,
        retailer="lidl",
        purchase_date=receipt_date,
        store=LIDL_STORE_NAME,
        address=_extract_lidl_address(soup, address),
    )
    receipt_data["payment_methods"] = _extract_lidl_payment_methods(soup)
    receipt_data.update(
        _extract_lidl_pos_metadata(
            soup,
            receipt_id=receipt_id,
            receipt_date=receipt_date,
        )
    )

    # Extract total price (amount to pay - "zu zahlen")
    try:
        # Method 1: Look for "zu zahlen" line and extract the amount from the same line
        purchase_summary_elements = soup.find_all(id=re.compile(r"^purchase_summary_"))
        for element in purchase_summary_elements:
            element_text = element.get_text().strip()
            if "zu zahlen" in element_text:
                # Find all spans with bold class in the same parent to get the amount
                parent = element.parent
                amount_spans = parent.find_all("span", class_="css_bold")
                for span in amount_spans:
                    span_text = span.get_text().strip()
                    # Look for a price pattern (digits,digits)
                    if re.match(r"^\d+,\d+$", span_text):
                        receipt_data["total_price"] = float(span_text.replace(",", "."))
                        break
                if receipt_data["total_price"]:
                    break
    except:
        # Fallback: Try the old method from purchase_tender_information_5
        try:
            total_element = soup.find(id="purchase_tender_information_5")
            if total_element:
                parts = total_element.get_text().strip().split()
                if len(parts) >= 2:
                    receipt_data["total_price"] = float(parts[-2].replace(",", "."))
        except:
            pass

    # Extract saved amount (only "Preisvorteil" and "Rabatt" lines, excluding "Lidl Plus Rabatt")
    try:
        total_regular_savings = 0.0

        # Get the purchase list text and search for discount lines
        try:
            purchase_list = soup.find("span", class_="purchase_list")
            if purchase_list:
                purchase_text = purchase_list.get_text()

                # Find all discount lines and extract the amounts
                lines = purchase_text.split("\n")
                # Regex to find monetary amount like -0,20 or - 0.20 or 0,20
                amount_regex = re.compile(r"-?\s*(\d+[\.,]\d{2})")
                pct_regex = re.compile(r"rabatt\s*(\d{1,3})\s*%")
                for line in lines:
                    line_stripped = line.strip()
                    line_lower = line_stripped.lower()

                    # Include "Preisvorteil" lines (exclude summary lines)
                    if "preisvorteil" in line_lower and "gesamter" not in line_lower:
                        amount_match = amount_regex.search(line_stripped)
                        if amount_match:
                            amount_str = amount_match.group(1)
                            amount_float = float(amount_str.replace(",", "."))
                            total_regular_savings += amount_float

                    # Exclude Lidl Plus Rabatt explicitly
                    elif "rabatt" in line_lower and "lidl plus rabatt" not in line_lower:
                        # Check for percent sticker like "RABATT 20%"
                        pct_match = pct_regex.search(line_lower)
                        amount_match = amount_regex.search(line_stripped)

                        if pct_match:
                            try:
                                pct_val = int(pct_match.group(1))
                                # record the percent (keep as int)
                                receipt_data.setdefault("sticker_discount_pct", []).append(pct_val)
                            except ValueError:
                                pass

                        # If a monetary amount is present on the same line, treat as sticker monetary saving
                        if amount_match:
                            amount_str = amount_match.group(1)
                            try:
                                amount_float = float(amount_str.replace(",", "."))
                                # accumulate into regular savings as well for backward compatibility TODO
                                #total_regular_savings += amount_float TODO
                                # also accumulate into sticker-specific total
                                # use a temp var to collect sticker amounts
                                if receipt_data.get("sticker_discount_amount") is None:
                                    receipt_data["sticker_discount_amount"] = 0.0
                                receipt_data["sticker_discount_amount"] += amount_float
                            except (ValueError, AttributeError):
                                pass
        except:
            pass

        # Set the saved_amount if we found any regular savings
        if total_regular_savings > 0:
            receipt_data["amount_saved"] = round(total_regular_savings, 2)
    except:
        pass

    # Extract Lidl Plus savings
    try:
        # Look for the "Mit Lidl Plus" box that shows "X,XX EUR gespart"
        try:
            # First, try to find the specific "EUR gespart" text in the VAT info section
            vat_info_elements = soup.find_all("span", class_="vat_info")
            for element in vat_info_elements:
                element_text = element.get_text().strip()
                if "EUR gespart" in element_text:
                    # Extract the amount before "EUR gespart"
                    amount_match = re.search(r"(\d+,\d+)\s+EUR gespart", element_text)
                    if amount_match:
                        receipt_data["lidlplus_amount_saved"] = float(
                            amount_match.group(1).replace(",", ".")
                        )
                        break
        except:
            # Fallback: search in the entire page for "EUR gespart"
            try:
                page_text = soup.get_text()
                gespart_match = re.search(r"(\d+,\d+)\s+EUR gespart", page_text)
                if gespart_match:
                    receipt_data["lidlplus_amount_saved"] = float(
                        gespart_match.group(1).replace(",", ".")
                    )
            except:
                pass
    except:
        pass

    if receipt_data.get("lidlplus_amount_saved") is None:
        receipt_data["lidlplus_amount_saved"] = 0.0

    return receipt_data


def _extract_lidl_address(
    soup: BeautifulSoup,
    fallback_address: Optional[dict] = None,
) -> dict:
    """Extract Lidl address data from visible header lines, with API fallback."""
    parsed_address = extract_address_from_lines(list(soup.stripped_strings)[:20])
    if parsed_address:
        return parsed_address
    return normalize_address(fallback_address)


def _extract_lidl_payment_methods(soup: BeautifulSoup) -> list[dict]:
    """Extract payment method data from the Lidl receipt summary/tender section."""
    payment_methods = []

    summary_method = _extract_lidl_summary_tender_description(soup)
    summary_amount = _extract_money_from_repeated_id(soup, "purchase_summary_3")

    tender_method_line = _extract_text_from_repeated_id(soup, "purchase_tender_information_3")
    tender_amount = _extract_money_from_repeated_id(soup, "purchase_tender_information_5")
    card_masked = _extract_text_from_repeated_id(soup, "purchase_tender_information_9")
    tender_details = _extract_text_from_repeated_id(soup, "purchase_tender_information_10")

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
    """Normalize stored Lidl payment method entries and drop known placeholder fields."""
    normalized_methods = []

    for payment_method in payment_methods or []:
        if not isinstance(payment_method, dict):
            continue

        method = _normalize_payment_value(payment_method.get("method"))
        amount = _extract_numeric_payment_amount(payment_method.get("amount"))
        if not method and not amount:
            continue

        normalized_method = {}
        if method:
            normalized_method["method"] = method
        if amount is not None:
            normalized_method["amount"] = amount

        network = _normalize_payment_value(payment_method.get("network"))
        if _is_meaningful_payment_network(network):
            normalized_method["network"] = network

        card_masked = _normalize_payment_value(payment_method.get("card_masked"))
        if _is_meaningful_payment_card_masked(card_masked, method):
            normalized_method["card_masked"] = card_masked

        details = _normalize_payment_value(payment_method.get("details"))
        if _is_meaningful_payment_details(details, amount, method):
            normalized_method["details"] = details

        normalized_methods.append(normalized_method)

    return normalized_methods


def _extract_lidl_summary_tender_description(
    soup: BeautifulSoup,
) -> Optional[str]:
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
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    if not normalized or normalized == ":":
        return None
    return normalized


def _extract_numeric_payment_amount(value: object) -> Optional[float]:
    """Normalize payment amounts to floats when a numeric amount is present."""
    normalized = _normalize_payment_value(value)
    if not normalized:
        return None

    match = re.search(r"(\d+[\.,]\d{1,2})", normalized)
    if not match:
        return None

    integer, decimals = re.split(r"[\.,]", match.group(1), maxsplit=1)
    return float(f"{integer}.{decimals.ljust(2, '0')}")


def _is_meaningful_payment_network(network: Optional[str]) -> bool:
    """Return True for non-placeholder payment network values."""
    return bool(network)


def _is_meaningful_payment_card_masked(
    card_masked: Optional[str],
    method: Optional[str],
) -> bool:
    """Return True when the stored card/terminal reference carries useful payment data."""
    if not card_masked:
        return False
    stripped = card_masked.lstrip(":").strip()
    if not stripped:
        return False
    if method and method.lower() == "lidl pay" and re.fullmatch(r"\d{1,3}", stripped):
        return False
    return True


def _is_meaningful_payment_details(
    details: Optional[str],
    amount: Optional[str],
    method: Optional[str],
) -> bool:
    """Return True when payment details contain more than a bare echoed amount placeholder."""
    if not details:
        return False
    stripped = details.lstrip(":").strip()
    if not stripped:
        return False
    if method and method.lower() == "lidl pay":
        amount_value = _parse_decimal_amount(amount)
        echoed_amount = _parse_decimal_amount(stripped)
        if amount_value is not None and echoed_amount is not None and amount_value == echoed_amount:
            return False
        if re.fullmatch(r"\d+(?:[\.,]\d{1,2})?\s*EUR", stripped, re.IGNORECASE):
            return False
    return True


def _parse_decimal_amount(value: Optional[str]) -> Optional[int]:
    """Parse a decimal currency value into cents for lightweight equality checks."""
    normalized = _normalize_payment_value(value)
    if not normalized:
        return None
    match = re.search(r"(\d+)(?:[\.,](\d{1,2}))?", normalized)
    if not match:
        return None
    euros = int(match.group(1))
    cents = (match.group(2) or "0")[:2].ljust(2, "0")
    return euros * 100 + int(cents)


def infer_lidl_pos_metadata_from_receipt_id(
    receipt_id: str,
    receipt_date: str,
) -> Optional[dict]:
    """Infer market/register/cashier from the Lidl receipt id when it matches the known pattern."""
    receipt_id = str(receipt_id or "")
    date_token = str(receipt_date or "").replace(".", "")
    if not receipt_id.startswith("2300") or not date_token:
        return None

    date_index = receipt_id.find(date_token)
    if date_index == -1:
        return None

    prefix = receipt_id[4:date_index]
    suffix = receipt_id[date_index + len(date_token):]
    if len(prefix) < 5:
        return None

    market = prefix[:4]
    register = prefix[4:]
    if not (market.isdigit() and register.isdigit() and suffix.isdigit()):
        return None

    return {
        "market": market,
        "register": register.zfill(2),
        "cashier": suffix.zfill(6),
    }


def _extract_lidl_pos_metadata(
    soup: BeautifulSoup,
    receipt_id: Optional[str] = None,
    receipt_date: Optional[str] = None,
) -> dict:
    """Extract market/register/cashier metadata from Lidl HTML with a receipt-id fallback."""
    pos_line = _extract_text_from_repeated_id(soup, "return_code_line_13")
    serial_line = _extract_text_from_repeated_id(soup, "return_code_line_3")

    metadata = {
        "market": None,
        "register": None,
        "cashier": None,
    }

    pos_match = LIDL_POS_LINE_RE.search(pos_line)
    if pos_match:
        metadata["market"] = pos_match.group("market")
        metadata["register"] = pos_match.group("register")
        metadata["cashier"] = pos_match.group("cashier")
        return metadata

    serial_match = LIDL_SERIAL_LINE_RE.search(serial_line)
    if serial_match:
        metadata["market"] = serial_match.group("market")
        metadata["register"] = serial_match.group("register")

    inferred_metadata = infer_lidl_pos_metadata_from_receipt_id(
        receipt_id or "",
        receipt_date or "",
    )
    if inferred_metadata:
        for field, value in inferred_metadata.items():
            if not metadata.get(field):
                metadata[field] = value

    return metadata


def _extract_text_from_repeated_id(soup: BeautifulSoup, element_id: str) -> str:
    """Join the visible text of all nodes sharing the same receipt line id."""
    parts = [element.get_text() for element in soup.find_all(id=element_id)]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _extract_money_from_repeated_id(soup: BeautifulSoup, element_id: str) -> Optional[float]:
    """Extract the first monetary value from a repeated receipt line id."""
    text = _extract_text_from_repeated_id(soup, element_id)
    match = re.search(r"(\d+,\d{2})", text)
    if match:
        return float(match.group(1).replace(",", "."))
    return None
