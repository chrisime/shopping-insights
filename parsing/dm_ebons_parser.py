"""Parse dm eBon details into the shared receipt schema.

dm eBons are delivered as JSON from ``/api/customer/ebons/<id>``. The detail
carries the store address, register, discount, payback points and a list of
purchased item identifiers (DAN). The original eBon PDF contains the full
itemized receipt (names, prices, quantities); when the workflow has parsed it,
those items are stored under ``pdfItems`` and take precedence over the DAN-only
``bonItems``.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

import requests

from config import DmConfig
from shared.receipt_schema import ReceiptData, build_receipt_schema

_STREET_NUMBER_RE = re.compile(r"^(?P<street>.+?)[ \t]+(?P<number>\d+[a-zA-Z]?)$")


def parse_dm_ebon(data: dict) -> ReceiptData:
    """Parse a dm eBon detail dict into the normalized receipt structure."""
    receipt_id = str(data.get("id") or "").strip()
    purchase_date = str(data.get("date") or "").strip() or None
    if not receipt_id or not purchase_date:
        raise ValueError("dm-eBon konnte nicht eindeutig identifiziert werden")

    address = _normalize_dm_address(data.get("address") or {})
    register = _optional_int_text(data.get("cashRegisterId"))
    items = _build_dm_items(data)
    discount = data.get("discount")
    payback_points = _optional_int(data.get("totalPaybackPoints"))

    return build_receipt_schema(
        receipt_id=receipt_id,
        retailer="dm",
        purchase_date=purchase_date,
        store=_optional_text((data.get("address") or {}).get("name")),
        address=address,
        register=register,
        discount=discount,
        total_price=data.get("totalAmount"),
        currency=str(data.get("currency") or "EUR"),
        dm_payback_points=payback_points,
        items=items,
        source_file=receipt_id,
    )


def enrich_dm_item_names(
    items: list[dict],
    session: requests.Session | None = None,
) -> list[dict]:
    """Best-effort DAN → product-name enrichment via the dm products gateway.

    Falls back to the eBon description or an empty name when the gateway is
    unavailable or the DAN cannot be resolved.
    """
    for item in items:
        name = str(item.get("name") or "").strip()
        if name:
            continue
        resolved = _resolve_product_name(str(item.get("dan") or ""), session)
        item["name"] = resolved or ""
    return items


def _resolve_product_name(dan: str, session: requests.Session | None) -> str | None:
    """Return a product name for ``dan`` or ``None`` when it cannot be resolved."""
    if not dan:
        return None
    try:
        active_session = session or requests.Session()
        response = active_session.get(
            DmConfig.get_product_url(dan),
            timeout=DmConfig.DEFAULT_TIMEOUT,
            headers={"User-Agent": DmConfig.DEFAULT_USER_AGENT},
        )
        if response.status_code != 200:
            return None
        data = response.json()
    except (requests.exceptions.RequestException, ValueError):
        logger.debug("dm-Produktauflösung für DAN %s fehlgeschlagen", dan)
        return None

    return _extract_product_name(data)


def _extract_product_name(data: object) -> str | None:
    """Extract a product name from common dm product JSON shapes."""
    if not isinstance(data, dict):
        return None
    for key in ("name", "title", "productName", "displayName"):
        value = data.get(key)
        if isinstance(value, dict):
            value = value.get("de") or value.get("text")
        text = _optional_text(value)
        if text:
            return text
    return None


def _build_dm_items(data: dict) -> list[dict]:
    """Build normalized item dicts, preferring parsed PDF items when present."""
    pdf_items = data.get("pdfItems") or []
    bon_items = data.get("bonItems") or []
    if pdf_items:
        return _merge_pdf_items_with_dans(pdf_items, bon_items)
    return _build_dan_items(bon_items)


def _merge_pdf_items_with_dans(pdf_items: list, bon_items: list) -> list[dict]:
    """Merge parsed PDF items with DANs from the API payload by position."""
    items: list[dict] = []
    for index, pdf_item in enumerate(pdf_items):
        if not isinstance(pdf_item, dict):
            continue
        item = dict(pdf_item)
        dan = ""
        if index < len(bon_items) and isinstance(bon_items[index], dict):
            dan = str(bon_items[index].get("dan") or "").strip()
        if dan:
            item["dan"] = dan
        items.append(item)
    return items


def _build_dan_items(bon_items: list) -> list[dict]:
    """Build normalized item dicts with the DAN preserved."""
    items: list[dict] = []
    for index, bon_item in enumerate(bon_items, start=1):
        if not isinstance(bon_item, dict):
            continue
        dan = str(bon_item.get("dan") or "").strip()
        if not dan:
            continue
        items.append(
            {
                "position": index,
                "name": str(bon_item.get("description") or "").strip() or "",
                "price": None,
                "quantity": 1,
                "unit": "stk",
                "dan": dan,
            }
        )
    return items


def _normalize_dm_address(address: dict) -> dict:
    """Map the dm address object onto the shared address schema."""
    street, street_no = _split_street_number(
        str(address.get("street") or "").strip()
    )
    normalized = {
        "street": street,
        "street_no": street_no,
        "zip": address.get("zip"),
        "city": _optional_text(address.get("city")),
    }
    return normalized


def _split_street_number(raw_street: str) -> tuple[str | None, str | None]:
    """Split ``Rudolf-Breitscheid-Straße 14`` into street and house number."""
    if not raw_street:
        return None, None
    match = _STREET_NUMBER_RE.match(raw_street)
    if match:
        return match.group("street").strip(), match.group("number").strip()
    return raw_street, None


def _optional_int_text(value: object) -> str | None:
    integer = _optional_int(value)
    return None if integer is None else str(integer)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None