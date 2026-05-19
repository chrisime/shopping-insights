"""Shared hash helpers for canonical receipt and source change detection."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

import simplejson


RECEIPT_HASH_METADATA_FIELDS = frozenset({"source_hash", "payload_hash"})
LIDL_SOURCE_HASH_FIELDS = (
    "id",
    "date",
    "isHtml",
    "currency",
    "total",
    "totalPrice",
    "totalAmount",
    "amountSaved",
    "savedAmount",
)
LIDL_SOURCE_HASH_STORE_FIELDS = (
    "id",
    "name",
    "street",
    "streetNo",
    "zip",
    "city",
)


def calculate_value_hash(value: Any) -> str:
    """Return a stable SHA-256 hash for any JSON-compatible value."""
    rendered = simplejson.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    text = "" if rendered is None else rendered
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def calculate_receipt_payload_hash(receipt_data: Mapping[str, Any]) -> str:
    """Return a stable content hash for a normalized receipt excluding hash metadata."""
    payload = {
        key: value
        for key, value in dict(receipt_data).items()
        if key not in RECEIPT_HASH_METADATA_FIELDS
    }
    return calculate_value_hash(payload)


def build_lidl_source_hash_payload(ticket_data: Mapping[str, Any]) -> dict[str, Any]:
    """Build a stable, minimal Lidl source projection used for delta detection."""
    payload: dict[str, Any] = {
        field_name: ticket_data[field_name]
        for field_name in LIDL_SOURCE_HASH_FIELDS
        if field_name in ticket_data
    }

    store = ticket_data.get("store")
    if isinstance(store, Mapping):
        store_payload = {
            field_name: store[field_name]
            for field_name in LIDL_SOURCE_HASH_STORE_FIELDS
            if field_name in store
        }
        if store_payload:
            payload["store"] = store_payload

    return payload


def calculate_lidl_source_hash(ticket_data: Mapping[str, Any]) -> str:
    """Return a stable change hash for the relevant Lidl ticket-list source fields."""
    return calculate_value_hash(build_lidl_source_hash_payload(ticket_data))

