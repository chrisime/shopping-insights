"""Main receipt HTML parser."""

from typing import Any, Dict

from bs4 import BeautifulSoup

from shared.lidl_ticket_dto import LidlTicketDTO
from shared.receipt_dates import normalize_purchase_date

from .lidl_info_extractor import extract_lidl_receipt_info
from .lidl_items_extractor import extract_lidl_receipt_items
from .lidl_totals_extractor import extract_lidl_totals


def parse_lidl_ticket(ticket: LidlTicketDTO, receipt_id: str = "") -> Dict[str, Any]:
    """Parse a Lidl ticket DTO into the normalized receipt structure."""
    # receipt_id parameter is kept for backward compatibility but unused since ticket.id is authoritative
    receipt_date = normalize_purchase_date(ticket.date)
    if receipt_date is None:
        raise ValueError("Kein gültiges Kaufdatum im Ticket vorhanden")

    if not ticket.html_receipt:
        raise ValueError("Kein HTML-Inhalt im Ticket vorhanden")

    address = ticket.store.to_address_dict() if ticket.store.has_address() else None

    soup = BeautifulSoup(ticket.html_receipt, "html.parser")
    receipt_data = extract_lidl_receipt_info(
        soup, ticket.id, receipt_date, ticket.store.name, address
    )
    receipt_data["items"] = extract_lidl_receipt_items(soup)

    totals = extract_lidl_totals(
        soup,
        discount=receipt_data.get("discount"),
        lidlplus_discount=receipt_data.get("lidlplus_discount"),
        sticker_discount=receipt_data.get("sticker_discount"),
    )

    if totals.discount is not None:
        receipt_data["discount"] = totals.discount
    if totals.saved_deposit is not None:
        receipt_data["saved_deposit"] = totals.saved_deposit
    for field_name, value in totals.additional_savings.items():
        receipt_data[field_name] = value
    return receipt_data
