"""Shared helpers for parsing and normalizing receipt purchase dates."""

from __future__ import annotations

from datetime import date, datetime, time
import re
from typing import Any

RETAILER_PURCHASE_DATE_FORMAT = "%d.%m.%Y"
NORMALIZED_PURCHASE_DATE_FORMAT = "%Y-%m-%d"
ISO_PURCHASE_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}$")


def parse_purchase_date(value: Any) -> datetime | None:
    """Parse supported receipt purchase dates into a datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)

    text = str(value).strip()
    if not text:
        return None

    for date_format in (RETAILER_PURCHASE_DATE_FORMAT, NORMALIZED_PURCHASE_DATE_FORMAT):
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue

    return None



def normalize_purchase_date(value: Any) -> str | None:
    """Normalize supported receipt purchase dates into ISO-8601 date text."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return None

    parsed = parse_purchase_date(text)
    if parsed is None:
        return None
    return parsed.date().isoformat()


def is_normalized_purchase_date(value: Any) -> bool:
    """Return True when the value is a valid normalized ISO purchase date."""
    if value is None:
        return False
    text = str(value).strip()
    if not text or ISO_PURCHASE_DATE_RE.fullmatch(text) is None:
        return False
    return parse_purchase_date(text) is not None


def normalize_purchase_date_from_receipt_id_token(value: Any) -> str | None:
    """Normalize compact receipt-id date tokens like ddmmyyyy into ISO purchase dates."""
    text = str(value or "").strip()
    if re.fullmatch(r"\d{8}", text) is None:
        return None
    return normalize_purchase_date(f"{text[:2]}.{text[2:4]}.{text[4:8]}")


