"""Shared helpers for canonical payment method normalization."""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional


METHOD_CARD = "Karte"
METHOD_CASH = "Bar"
METHOD_REWE_BONUS = "Bonus-Guthaben"
METHOD_LIDL_PAY = "Lidl Pay"

NETWORK_REWE = "REWE"
NETWORK_LIDL = "LIDL"

EMPTY_TEXT_MARKERS = {":"}
REWE_PAYMENT_HINT_TOKENS = {"bonus-guthaben", "bonus guthaben"}
LIDL_PAYMENT_HINT_FRAGMENT = "lidl"
REWE_PAYMENT_HINT_FRAGMENT = "rewe"


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
    "bar": METHOD_CASH,
    "bonus-guthaben": METHOD_REWE_BONUS,
    "bonus guthaben": METHOD_REWE_BONUS,
    "lidl pay": METHOD_LIDL_PAY,
}

RETAILER_NETWORK_ALIASES = {
    "lidl": NETWORK_LIDL,
    "rewe": NETWORK_REWE,
}


def normalize_payment_method_entry(payment_method: Mapping[str, Any]) -> Optional[dict]:
    """Normalize a payment method entry to the canonical stored schema."""
    method = _normalize_text(payment_method.get("method"))
    network = _normalize_text(payment_method.get("network"))
    amount = _normalize_money_value(payment_method.get("amount"))
    retailer = payment_method.get("retailer")
    label = method or network

    if not label and amount is None:
        return None

    normalized: dict[str, Any] = {}
    if not label:
        if amount is not None:
            normalized["amount"] = amount
        return normalized

    card_network = _lookup_card_network(method) or _lookup_card_network(network)
    if card_network:
        normalized["method"] = METHOD_CARD
        normalized["network"] = card_network
    else:
        canonical_method = _lookup_method_alias(label)
        if canonical_method == METHOD_CASH:
            normalized["method"] = METHOD_CASH
        else:
            normalized["method"] = canonical_method or label
            retailer_network = _detect_retailer_network(retailer, method, network)
            if retailer_network:
                normalized["network"] = retailer_network

    if amount is not None:
        normalized["amount"] = amount
    return normalized


def _lookup_card_network(value: Optional[str]) -> Optional[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return None
    return CARD_NETWORK_ALIASES.get(normalized.lower())


def _lookup_method_alias(value: str) -> Optional[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return None
    normalized_key = normalized.lower()
    if normalized_key in METHOD_ALIASES:
        return METHOD_ALIASES[normalized_key]
    if normalized_key in CARD_METHOD_LABELS:
        return METHOD_CARD
    return None


def _detect_retailer_network(retailer: Optional[str], method: Optional[str], network: Optional[str]) -> Optional[str]:
    normalized = _normalize_text(retailer)
    if normalized:
        explicit_retailer = RETAILER_NETWORK_ALIASES.get(normalized.lower())
        if explicit_retailer is not None:
            return explicit_retailer

    for value in (method, network):
        if not value:
            continue
        lowered = value.lower()
        if LIDL_PAYMENT_HINT_FRAGMENT in lowered:
            return NETWORK_LIDL
        if REWE_PAYMENT_HINT_FRAGMENT in lowered or lowered in REWE_PAYMENT_HINT_TOKENS:
            return NETWORK_REWE

    return None


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    if not normalized or normalized in EMPTY_TEXT_MARKERS:
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

    match = re.search(r"-?\d+(?:[.,]\d{1,2})?", normalized)
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
