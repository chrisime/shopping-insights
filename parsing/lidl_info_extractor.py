"""Extract basic receipt information from HTML content."""

import re
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup

from shared.receipt_schema import build_receipt_schema
from shared.addresses import normalize_address
from shared.payment_methods import normalize_payment_method_entry

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

    _apply_lidl_payment_methods(receipt_data, soup)

    _apply_lidl_pos_metadata(
        receipt_data,
        soup,
        receipt_id=receipt_id,
        receipt_date=receipt_date,
    )

    _apply_lidl_total_price(receipt_data, soup)

    _apply_lidl_discount_fields(receipt_data, soup)

    _apply_lidl_plus_discount(receipt_data, soup)

    return receipt_data


def _apply_lidl_plus_discount(receipt_data, soup):
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


def _extract_lidl_address(soup: BeautifulSoup, fallback_address: Optional[dict] = None,) -> dict:
    """Extract Lidl address data from visible header lines, with API fallback."""
    parsed_address = extract_address_from_lines(list(soup.stripped_strings)[:20])
    if parsed_address:
        return parsed_address
    return normalize_address(fallback_address)


def _apply_lidl_total_price(receipt_data: Dict[str, Any], soup: BeautifulSoup) -> None:
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
                price = _parse_lidl_money_value(span.get_text())
                if price is not None:
                    receipt_data["total_price"] = price
                    return
    except Exception:
        pass

    tender_amount = _extract_money_from_repeated_id(soup, "purchase_tender_information_5")
    if tender_amount is not None:
        receipt_data["total_price"] = tender_amount


def _apply_lidl_discount_fields(receipt_data: Dict[str, Any], soup: BeautifulSoup) -> None:
    """Extract and classify regular and sticker-like discounts from the purchase list text."""
    try:
        purchase_list = soup.find("span", class_="purchase_list")
        if not purchase_list:
            return

        total_regular_savings = 0.0
        total_sticker_savings = 0.0
        sticker_percentages: list[int] = []

        for line in purchase_list.get_text().split("\n"):
            parsed_line = _parse_lidl_discount_line(line)
            if not parsed_line:
                continue

            if parsed_line["kind"] == "preisvorteil":
                total_regular_savings += parsed_line["amount"]
                continue

            if parsed_line["kind"] == "sticker":
                sticker_percentages.append(parsed_line["percent"])
                total_sticker_savings += parsed_line["amount"]

        if total_regular_savings > 0:
            receipt_data["amount_saved"] = round(total_regular_savings, 2)
        if sticker_percentages:
            receipt_data["sticker_discount_pct"] = sticker_percentages
        if total_sticker_savings > 0:
            receipt_data["sticker_discount_amount"] = round(total_sticker_savings, 2)
    except Exception:
        pass


def _parse_lidl_discount_line(line: object) -> Optional[Dict[str, Any]]:
    """Classify a Lidl discount line into a known discount kind with parsed values."""
    line_text = str(line or "").strip()
    if not line_text:
        return None

    line_lower = line_text.lower()
    amount_match = re.search(r"-?\s*(\d+[\.,]\d{2})", line_text)
    amount = float(amount_match.group(1).replace(",", ".")) if amount_match else None

    if "preisvorteil" in line_lower and "gesamter" not in line_lower and amount is not None:
        return {"kind": "preisvorteil", "amount": amount}

    if "lidl plus rabatt" in line_lower:
        return None

    pct_match = re.search(r"rabatt\s*(\d{1,3})\s*%", line_lower)
    if pct_match and amount is not None:
        try:
            return {"kind": "sticker", "amount": amount, "percent": int(pct_match.group(1))}
        except ValueError:
            return None

    return None


def _apply_lidl_payment_methods(receipt_data: Dict[str, Any], soup: BeautifulSoup) -> None:
    """Apply payment method data from the Lidl receipt summary/tender section."""
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

    receipt_data["payment_methods"] = normalize_lidl_payment_methods(payment_methods)


def normalize_lidl_payment_methods(payment_methods: list[dict]) -> list[dict]:
    """Normalize stored Lidl payment method entries to the canonical schema."""
    normalized_methods = []

    for payment_method in payment_methods or []:
        if not isinstance(payment_method, dict):
            continue

        normalized_method = normalize_payment_method_entry(
            {
                "method": payment_method.get("method"),
                "network": payment_method.get("network"),
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



def infer_lidl_pos_metadata_from_receipt_id(receipt_id: str, receipt_date: str) -> Optional[dict]:
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


def _apply_lidl_pos_metadata(
    receipt_data: Dict[str, Any],
    soup: BeautifulSoup,
    receipt_id: Optional[str] = None,
    receipt_date: Optional[str] = None,
) -> None:
    """Apply market/register/cashier metadata from Lidl HTML with a receipt-id fallback."""
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
        receipt_data.update(metadata)
        return

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

    receipt_data.update(metadata)


def _extract_text_from_repeated_id(soup: BeautifulSoup, element_id: str) -> str:
    """Join the visible text of all nodes sharing the same receipt line id."""
    parts = [element.get_text() for element in soup.find_all(id=element_id)]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _extract_money_from_repeated_id(soup: BeautifulSoup, element_id: str) -> Optional[float]:
    """Extract the first monetary value from a repeated receipt line id."""
    text = _extract_text_from_repeated_id(soup, element_id)
    return _parse_lidl_money_value(text)


def _parse_lidl_money_value(text: object) -> Optional[float]:
    """Parse the first Lidl-style decimal money value from arbitrary text."""
    match = re.search(r"(\d+,\d{2})", str(text or ""))
    if not match:
        return None
    return float(match.group(1).replace(",", "."))
