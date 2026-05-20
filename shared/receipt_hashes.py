"""Shared hash helpers for canonical receipt payloads."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

import simplejson


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
        if key not in frozenset({"payload_hash"})
    }
    return calculate_value_hash(payload)
