"""Extract dm eBon items from PDF text.

The dm API only returns DAN identifiers without names or prices, but the
original eBon PDF contains the full itemized receipt. This module parses the
PDF text to recover item names, prices and quantities.

Two line formats appear on dm eBons:

- Single item: ``dmBio Buchweizenmehl 500 g 1,95 2``
  (name, price, tax class)
- Multi-quantity item: ``3x 1,75 dmBio Buchweizenmehl 5 5,25 2``
  (quantity, unit price, name, total, tax class)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pdfplumber

from shared.float_parser import parse_german_float
from shared.receipt_schema import build_receipt_item


MULTI_ITEM_RE = re.compile(
    r"^(?P<qty>\d+)x\s+(?P<unit_price>\d+,\d{2})\s+(?P<name>.+?)\s+"
    r"(?P<total>\d+,\d{2})\s+(?P<tax>\d)$"
)
SINGLE_ITEM_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<price>\d+,\d{2})\s+(?P<tax>\d)$"
)


def extract_dm_pdf_items(pdf_path: str | Path) -> list[dict[str, Any]]:
    """Extract normalized item dicts from a dm eBon PDF.

    Returns an empty list when the PDF contains no parseable item lines.
    """
    path = Path(pdf_path)
    with pdfplumber.open(path) as pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return _parse_dm_item_lines(lines)


def _parse_dm_item_lines(lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in lines:
        item = _parse_item_line(line)
        if item is not None:
            items.append(item)
    return items


def _parse_item_line(line: str) -> dict[str, Any] | None:
    """Parse one dm eBon line into a normalized item dict or ``None``."""
    multi = MULTI_ITEM_RE.match(line)
    if multi:
        quantity = int(multi.group("qty"))
        unit_price = parse_german_float(multi.group("unit_price"))
        name = _normalize_name(multi.group("name"))
        return build_receipt_item(
            name=name,
            price=unit_price,
            quantity=quantity,
            unit="stk",
        )

    single = SINGLE_ITEM_RE.match(line)
    if single:
        price = parse_german_float(single.group("price"))
        name = _normalize_name(single.group("name"))
        return build_receipt_item(
            name=name,
            price=price,
            quantity=1,
            unit="stk",
        )

    return None


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()