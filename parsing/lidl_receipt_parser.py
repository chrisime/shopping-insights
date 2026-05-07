"""Main receipt HTML parser."""

from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from .lidl_info_extractor import extract_lidl_receipt_info
from .lidl_items_extractor import extract_lidl_receipt_items
from .lidl_totals_preprocessor import extract_lidl_totals_input
from .lidl_totals_extractor import extract_lidl_totals


def parse_lidl_ticket(
    ticket_data: Dict[str, Any],
    receipt_id: str,
) -> Dict[str, Any]:
    """Parse a raw Lidl ticket payload into the normalized receipt structure."""
    receipt_date = ticket_data["date"][:10].replace("-", ".")

    address = None
    if isinstance(ticket_data.get("store"), dict):
        store = ticket_data["store"].get("name", "Unknown")
        address = _extract_lidl_store_address(ticket_data["store"])
    else:
        store = ticket_data.get("store", "Unknown")

    html_content = ticket_data.get("htmlPrintedReceipt", "")
    if not html_content:
        raise ValueError("Kein HTML-Inhalt im Ticket vorhanden")

    return parse_lidl_receipt_html(
        html_content,
        receipt_id,
        receipt_date,
        store,
        address,
    )


def parse_lidl_receipt_html(
    html_content: str,
    receipt_id: str,
    receipt_date: str,
    store: str,
    address: Optional[dict] = None,
) -> Dict[str, Any]:
    """Parse Lidl receipt HTML into the normalized receipt structure."""
    soup = BeautifulSoup(html_content, "html.parser")

    receipt_data = extract_lidl_receipt_info(
        soup, receipt_id, receipt_date, store, address
    )
    receipt_data["items"] = extract_lidl_receipt_items(soup)

    totals_input = extract_lidl_totals_input(
        soup,
        receipt_data.get("items", []),
        amount_saved=receipt_data.get("amount_saved"),
        lidlplus_amount_saved=receipt_data.get("lidlplus_amount_saved"),
        sticker_discount_amount=receipt_data.get("sticker_discount_amount"),
    )

    totals_result = extract_lidl_totals(
        total_no_saving=totals_input.total_no_saving,
        amount_saved=totals_input.amount_saved,
        lidlplus_amount_saved=totals_input.lidlplus_amount_saved,
        sticker_discount_amount=totals_input.sticker_discount_amount,
        saved_deposit=totals_input.saved_deposit,
    )
    if totals_result.total_price_no_saving is not None:
        receipt_data["total_price_no_saving"] = totals_result.total_price_no_saving
    if totals_result.amount_saved is not None:
        receipt_data["amount_saved"] = totals_result.amount_saved
    if totals_result.saved_deposit is not None:
        receipt_data["saved_deposit"] = totals_result.saved_deposit
    for field_name, value in totals_result.additional_savings.items():
        receipt_data[field_name] = value
    if totals_result.total_price is not None:
        receipt_data["total_price"] = totals_result.total_price

    return receipt_data


def _extract_lidl_store_address(
    store_payload: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Build a best-effort structured address from the Lidl API store payload."""
    street = (
        store_payload.get("street")
        or store_payload.get("streetName")
        or store_payload.get("addressLine1")
    )
    street_no = (
        store_payload.get("street_no")
        or store_payload.get("streetNo")
        or store_payload.get("houseNumber")
        or store_payload.get("house_no")
    )
    zip_code = (
        store_payload.get("zip")
        or store_payload.get("zipCode")
        or store_payload.get("postalCode")
    )
    city = store_payload.get("city") or store_payload.get("town")

    if not any((street, street_no, zip_code, city)):
        return None

    return {
        "street": street,
        "street_no": street_no,
        "zip": zip_code,
        "city": city,
    }
