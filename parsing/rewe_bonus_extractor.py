"""Extract REWE bonus amounts from PDF text."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from shared.float_parser import parse_german_float


REWE_BONUS_AMOUNT_RE = re.compile(
    r"Mit diesem Einkauf hast du\s+(?P<amount>\d+,\d{2})\s+EUR\s+"
    r"REWE Bonus-Guthaben gesammelt:",
    re.IGNORECASE,
)
REWE_TOTAL_BONUS_AMOUNT_RE = re.compile(
    r"Aktuelles Bonus-Guthaben:\s*(?P<amount>\d+,\d{2})\s+EUR",
    re.IGNORECASE,
)


def extract_bonus_amounts_from_text(text: str) -> Tuple[float, Optional[float]]:
    """Extract collected and total REWE bonus amounts from the raw PDF text."""
    bonus_match = REWE_BONUS_AMOUNT_RE.search(text)
    total_bonus_match = REWE_TOTAL_BONUS_AMOUNT_RE.search(text)
    return (
        parse_german_float(bonus_match.group("amount")) if bonus_match else 0.0,
        parse_german_float(total_bonus_match.group("amount")) if total_bonus_match else None,
    )
