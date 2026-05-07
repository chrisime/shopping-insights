"""Neutrale Adress-Schema-Helfer für Bondaten."""

from __future__ import annotations

import re
from typing import Optional


ADDRESS_FIELDS = ("street", "street_no", "zip", "city")


def empty_address() -> dict:
    """Return the canonical empty address object used in receipt JSON."""
    return {
        "street": None,
        "street_no": None,
        "zip": None,
        "city": None,
    }


def normalize_address(address: object) -> dict:
    """Normalize arbitrary address-like input to the canonical schema object."""
    normalized = empty_address()
    if not isinstance(address, dict):
        return normalized

    for field in ("street", "street_no", "city"):
        value = address.get(field)
        if value is None:
            continue
        text = str(value).strip()
        normalized[field] = text or None

    zip_value = address.get("zip")
    normalized["zip"] = _normalize_zip(zip_value)
    return normalized


def _normalize_zip(value: object) -> Optional[int]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if not re.fullmatch(r"\d{5}", text):
        return None
    return int(text)

