"""Shared helpers for parsing German-format decimal numbers."""

from typing import Any, Optional
import re


def parse_german_float(value: Any) -> Optional[float]:
    """Parse a German-format decimal string to float.

    Handles ``3,99``, ``1.234,56``, and already-numeric values.
    Returns ``None`` when the value cannot be parsed.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).strip()
    if not normalized:
        return None

    try:
        return float(normalized)
    except ValueError:
        pass

    match = re.search(r"-?\d[\d.]*(?:,\d+)?", normalized.replace("\u202f", "").replace("\xa0", ""))
    if not match:
        return None

    number_text = match.group(0)
    if "," in number_text and "." in number_text:
        if number_text.rfind(",") > number_text.rfind("."):
            number_text = number_text.replace(".", "").replace(",", ".")
        else:
            number_text = number_text.replace(",", "")
    else:
        number_text = number_text.replace(",", ".")

    try:
        return float(number_text)
    except ValueError:
        return None


def parse_amount_to_cents(value: Any) -> Optional[int]:
    """Parse a monetary value to cents for validation purposes.

    Handles ``3.99``, ``3,99``, ``1.234,56`` etc.
    Returns ``None`` when the value cannot be parsed.
    """
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None

    match = re.search(r"(\d+)(?:[.,](\d{1,2}))?", normalized)
    if not match:
        return None
    euros = int(match.group(1))
    cents = (match.group(2) or "0")[:2].ljust(2, "0")
    return euros * 100 + int(cents)
