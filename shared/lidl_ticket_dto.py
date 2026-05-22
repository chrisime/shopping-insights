"""Typed DTOs for Lidl API ticket responses.

Maps the raw nested JSON from the Lidl ticket endpoints into flat,
typed dataclasses so downstream code never touches raw dicts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LidlTicketsPageDTO:
    """Typed pagination response from get_tickets_page."""

    receipt_ids: list[str]
    page: int
    total_count: int

    @staticmethod
    def from_api_response(data: Dict[str, Any], page: int = 1) -> Optional[LidlTicketsPageDTO]:
        """Build a DTO from the raw API response."""
        if not isinstance(data, dict):
            return None

        raw_items = data.get("items", [])
        if not isinstance(raw_items, list):
            return None

        # Extract receipt IDs from items that have HTML receipts
        ids = []
        for item in raw_items:
            # Handle nested 'ticket' key
            if isinstance(item, dict) and "ticket" in item:
                inner_item = item["ticket"]
            else:
                inner_item = item

            if isinstance(inner_item, dict):
                receipt_id = str(inner_item.get("id") or "")
                has_html = bool(inner_item.get("isHtml", False))
                if receipt_id and has_html:
                    ids.append(receipt_id)

        return LidlTicketsPageDTO(
            receipt_ids=ids,
            page=page,
            total_count=data.get("totalCount", len(ids)),
        )


STREET_WITH_NUMBER_RE = re.compile(
    r"^(?P<street>.+?)\s*(?P<street_no>\d+[A-Za-z]?(?:\s*[-/]\s*\d+[A-Za-z]?)?)$"
)


@dataclass(frozen=True)
class LidlStoreDTO:
    """Structured Lidl store/filial info from the API."""

    name: str
    street: str | None
    street_no: str | None
    zip: str | None
    city: str | None

    def to_address_dict(self) -> dict[str, Any]:
        """Convert to the shared address dict format."""
        return {
            "street": self.street,
            "street_no": self.street_no,
            "zip": self.zip,
            "city": self.city,
        }

    def has_address(self) -> bool:
        return any((self.street, self.street_no, self.zip, self.city))


@dataclass(frozen=True)
class LidlTicketDTO:
    """Typed representation of a single Lidl ticket from the API.

    Created once from the raw API dict; the rest of the pipeline works
    with this immutable DTO instead of digging through nested dicts.
    """

    id: str
    date: str
    html_receipt: str
    store: LidlStoreDTO

    @staticmethod
    def from_api_response(ticket_data: Dict[str, Any], receipt_id: str = "") -> LidlTicketDTO:
        """Build a DTO from the raw ticket dict returned by ``get_lidl_ticket``.

        ``ticket_data`` is the ``data["ticket"]`` portion of the API response,
        as returned by :func:`api.lidl_client.get_lidl_ticket`.
        """
        ticket_id = str(ticket_data.get("id") or receipt_id or "")
        date = str(ticket_data.get("date") or "")
        html_receipt = str(ticket_data.get("htmlPrintedReceipt") or "")
        store = _extract_store(ticket_data)

        return LidlTicketDTO(
            id=ticket_id,
            date=date,
            html_receipt=html_receipt,
            store=store,
        )

    def to_api_dict(self) -> Dict[str, Any]:
        """Serialize the DTO back to the raw API dict format for storage."""
        return {
            "id": self.id,
            "date": self.date,
            "htmlPrintedReceipt": self.html_receipt,
            "store": self.store.to_address_dict() if self.store.has_address() else {},
        }


def _extract_store(ticket_data: Dict[str, Any]) -> LidlStoreDTO:
    """Extract store info from the ticket payload, handling multiple formats."""
    raw_store = ticket_data.get("store")

    if isinstance(raw_store, dict):
        return _parse_store_dict(raw_store)

    if isinstance(raw_store, str) and raw_store.strip():
        return LidlStoreDTO(name=raw_store.strip(), street=None, street_no=None, zip=None, city=None)

    return LidlStoreDTO(name="Lidl", street=None, street_no=None, zip=None, city=None)


def _parse_store_dict(store_payload: Dict[str, Any]) -> LidlStoreDTO:
    """Parse the nested store dict into a typed DTO.

    The API provides address as a single combined string (e.g. ``"Fronmüllerstr. 12"``),
    so we split it into street + street_no.
    """
    name = str(store_payload.get("name") or "Lidl").strip()

    street, street_no = _split_address_line(
        store_payload.get("address")
        or store_payload.get("street")
        or store_payload.get("streetName")
        or store_payload.get("addressLine1")
    )

    if not street_no:
        street_no = (
            store_payload.get("street_no")
            or store_payload.get("streetNo")
            or store_payload.get("houseNumber")
            or store_payload.get("house_no")
        )
        if street_no:
            street_no = str(street_no).strip()

    zip_code = str(
        store_payload.get("postalCode")
        or store_payload.get("zip")
        or store_payload.get("zipCode")
    ).strip()

    city = str(
        store_payload.get("locality")
        or store_payload.get("city")
        or store_payload.get("town")
    ).strip()

    return LidlStoreDTO(
        name=name,
        street=street if street else None,
        street_no=street_no if street_no else None,
        zip=zip_code if zip_code else None,
        city=city if city else None,
    )


def _split_address_line(address_line: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split ``'Fronmüllerstr. 12'`` into ``('Fronmüllerstr.', '12')``."""
    if not address_line or not isinstance(address_line, str):
        return None, None

    address_line = address_line.strip()
    match = STREET_WITH_NUMBER_RE.fullmatch(address_line)
    if match:
        return match.group("street").strip(), re.sub(r"\s+", "", match.group("street_no").strip())

    return address_line, None

