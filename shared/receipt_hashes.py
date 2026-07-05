"""Shared hash helpers for canonical receipt payloads."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

import simplejson


def calculate_receipt_payload_hash(receipt_data: Mapping[str, Any]) -> str:
    """Return a stable content hash for a normalized receipt excluding hash metadata."""
    payload = {key: value for key, value in receipt_data.items() if key != "payload_hash"}
    canonical_payload = simplejson.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
