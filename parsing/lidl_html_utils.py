"""Shared HTML extraction helpers for Lidl receipt parsing."""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

from shared.float_parser import parse_german_float


def extract_text_from_repeated_id(soup: BeautifulSoup, element_id: str) -> str:
    """Join the visible text of all nodes sharing the same receipt line id."""
    parts = [element.get_text() for element in soup.find_all(id=element_id)]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def extract_money_from_repeated_id(soup: BeautifulSoup, element_id: str) -> Optional[float]:
    """Extract the first monetary value from a repeated receipt line id."""
    text = extract_text_from_repeated_id(soup, element_id)
    return parse_german_float(text)
