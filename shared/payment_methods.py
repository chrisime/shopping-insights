"""Shared helpers for canonical payment method normalization."""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional


CARD_NETWORK_ALIASES = {
    "visa": "VISA",
    "mastercard": "Mastercard",
    "master card": "Mastercard",
    "amex": "Amex",
    "american express": "Amex",
    "girocard": "Girocard",
    "ec": "EC",
}

CARD_METHOD_LABELS = {
    "karte",
    "kreditkarte",
    "debitkarte",
    "ec-karte",
    "zahlungskarte",
}

METHOD_ALIASES = {
    "bar": "Bar",
    "bonus-guthaben": "Bonus-Guthaben",
    "bonus guthaben": "Bonus-Guthaben",
    "lidl pay": "Lidl Pay",
}


def normalize_payment_method_entry(payment_method: Mapping[str, Any]) -> Optional[dict]:
    """Normalize a payment method entry to the canonical stored schema."""
    method = _normalize_text(payment_method.get("method"))
    network = _canonicalize_network(payment_method.get("network"))
    amount = _normalize_money_value(payment_method.get("amount"))

    method, network = _canonicalize_method_and_network(method, network)
    if not method and network:
        method = "Karte"

    if not method and amount is None:
        return None

    normalized: dict[str, Any] = {}
    if method:
        normalized["method"] = method
    if network:
        normalized["network"] = network
    if amount is not None:
        normalized["amount"] = amount
    return normalized


def _canonicalize_method_and_network(
    method: Optional[str],
    network: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    if not method:
        return method, network

    method_key = method.lower()
    if method_key in METHOD_ALIASES:
        canonical_method = METHOD_ALIASES[method_key]
        if canonical_method == "Lidl Pay" and network == canonical_method:
            network = None
        return canonical_method, network

    if method_key in CARD_METHOD_LABELS:
        return "Karte", network

    method_as_network = _canonicalize_network(method)
    if method_as_network:
        return "Karte", network or method_as_network

    return method, network


def _canonicalize_network(value: object) -> Optional[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return None
    return CARD_NETWORK_ALIASES.get(normalized.lower(), normalized)


def _normalize_text(value: object) -> Optional[str]:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    if not normalized or normalized == ":":
        return None
    return normalized


def _normalize_money_value(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)

    normalized = str(value).strip()
    if not normalized:
        return None

    match = re.search(r"-?\d+(?:[\.,]\d{1,2})?", normalized)
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
        return round(float(number_text), 2)
    except ValueError:
        return None

