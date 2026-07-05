"""Main receipt HTML parser."""

from bs4 import BeautifulSoup

from shared.lidl_ticket_dto import LidlTicketDTO
from shared.receipt_dates import normalize_purchase_date
from shared.receipt_schema import ReceiptData, build_receipt_schema

from .lidl_info_extractor import extract_lidl_receipt_info
from .lidl_items_extractor import extract_lidl_receipt_items
from .lidl_totals_extractor import extract_lidl_totals


def parse_lidl_ticket(ticket: LidlTicketDTO) -> ReceiptData:
    """Parse a Lidl ticket DTO into the normalized receipt structure."""
    receipt_date = normalize_purchase_date(ticket.date)
    if receipt_date is None:
        raise ValueError("Kein gültiges Kaufdatum im Ticket vorhanden")

    if not ticket.html_receipt:
        raise ValueError("Kein HTML-Inhalt im Ticket vorhanden")

    address = ticket.store.to_address_dict() if ticket.store.has_address() else None

    soup = BeautifulSoup(ticket.html_receipt, "html.parser")
    raw = extract_lidl_receipt_info(
        soup, ticket.id, ticket.store.name, address
    )

    receipt_data = build_receipt_schema(
        receipt_id=ticket.id,
        retailer="lidl",
        purchase_date=receipt_date,
        store=raw.get("store"),
        address=raw.get("address"),
        payment_methods=raw.get("payment_methods", []),
        market=raw.get("market"),
        register=raw.get("register"),
        cashier=raw.get("cashier"),
        bon_number=raw.get("bon_number"),
        total_price=raw.get("total_price"),
        discount=raw.get("discount"),
        lidlplus_discount=raw.get("lidlplus_discount"),
        sticker_discount=raw.get("sticker_discount"),
        sticker_discount_pct=raw.get("sticker_discount_pct", []),
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
