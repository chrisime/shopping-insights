"""Extract REWE payment methods from PDF text."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from shared.float_parser import parse_german_float
from shared.payment_methods import normalize_payment_method_entry


PAYMENT_RE = re.compile(r"^Geg\.\s+(?P<method>.+?)\s+EUR\s+(?P<amount>-?\d+,\d{2})$")


def extract_payment_methods_from_lines(lines: List[str]) -> Tuple[List[Dict[str, Any]], float]:
    """Extract REWE payment methods and total redeemed bonus amount.

    Returns (payment_methods, rewe_bonus_saved_amount).
    """
    payment_methods: List[Dict[str, Any]] = []
    rewe_bonus_saved_amount = 0.0
    for line in lines:
        payment_match = PAYMENT_RE.match(line)
        if not payment_match:
            continue
        method = payment_match.group("method").strip()
        amount = payment_match.group("amount")
        numeric_amount = parse_german_float(amount)
        normalized_method = normalize_payment_method_entry(
            {
                "method": method,
                "retailer": "rewe",
                "amount": numeric_amount,
            }
        )
        if normalized_method:
            payment_methods.append(normalized_method)
        if _is_rewe_bonus_payment_method(method):
            rewe_bonus_saved_amount += numeric_amount
    return payment_methods, rewe_bonus_saved_amount


def _is_rewe_bonus_payment_method(method: str) -> bool:
    normalized_method = method.strip().lower()
    return "bonus" in normalized_method and "guthaben" in normalized_method
