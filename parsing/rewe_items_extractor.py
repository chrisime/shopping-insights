"""Extract REWE receipt items, discounts and deposit returns from PDF lines."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List

from shared.receipt_schema import build_receipt_item
from .rewe_parser_common import to_rewe_float


ITEM_LINE_RE = re.compile(r"^(?P<name>.+?)\s+(?P<amount>-?\d+,\d{2})\s+(?P<tax>[A-Z])(?:\s+\*)?$")
QUANTITY_LINE_RE = re.compile(
    r"^(?P<quantity>-?\d+(?:,\d+)?)\s*(?P<unit>Stk|kg)\s*x\s*"
    r"(?P<unit_price>-?\d+,\d{2})(?:\s*EUR/kg)?$"
)
SUM_RE = re.compile(r"SUMME EUR\s+(?P<amount>\d+,\d{2})")
SEPARATOR_PREFIXES = ("-----", "=====", "*****")
DEPOSIT_RETURN_PREFIXES = ("LEERG.", "LEERGUT")


@dataclass(frozen=True)
class ReweItemsExtractionResult:
    """Structured result for parsed REWE items and savings aggregates."""

    items: List[Dict[str, Any]]
    saved_amount: float
    saved_deposit: float


def extract_rewe_receipt_items(lines: List[str]) -> ReweItemsExtractionResult:
    """Extract normalized items and aggregate discount/deposit amounts."""
    items: List[Dict[str, Any]] = []
    saved_amount = 0.0
    saved_pfand = 0.0

    body_lines = _extract_receipt_body_lines(lines)
    index = 0
    while index < len(body_lines):
        line = body_lines[index]
        item_match = ITEM_LINE_RE.match(line)
        if not item_match:
            index += 1
            continue

        name = _normalize_item_name(item_match.group("name"))
        amount_text = item_match.group("amount")
        total_amount = to_rewe_float(amount_text)

        quantity_value: Any = 1
        unit = "stk"
        price_value = amount_text.lstrip("-")

        next_line = body_lines[index + 1] if index + 1 < len(body_lines) else None
        quantity_match = QUANTITY_LINE_RE.match(next_line or "")
        if quantity_match:
            quantity_value = quantity_match.group("quantity")
            unit = quantity_match.group("unit").lower()
            price_value = quantity_match.group("unit_price").lstrip("-")
            index += 1

        if total_amount < 0:
            if _is_deposit_return(name):
                saved_pfand += abs(total_amount)
            else:
                saved_amount += abs(total_amount)
            index += 1
            continue

        items.append(
            build_receipt_item(
                name=name,
                price=price_value,
                quantity=quantity_value,
                unit=unit,
            )
        )
        index += 1

    return ReweItemsExtractionResult(
        items=items,
        saved_amount=saved_amount,
        saved_deposit=saved_pfand,
    )

def _extract_receipt_body_lines(lines: List[str]) -> List[str]:
    try:
        start_index = lines.index("EUR") + 1
    except ValueError:
        start_index = 0

    sum_index = next(
        (index for index, line in enumerate(lines) if SUM_RE.match(line)),
        len(lines),
    )
    body_end = sum_index
    for index in range(sum_index - 1, start_index - 1, -1):
        if _is_separator(lines[index]):
            body_end = index
            break

    return lines[start_index:body_end]


def _normalize_item_name(name: str) -> str:
    normalized = re.sub(r"\s+", " ", name).strip()
    if normalized.startswith("PFAND ") and " EUR" in normalized:
        return "PFAND"
    return normalized


def _is_deposit_return(name: str) -> bool:
    upper_name = name.upper()
    return upper_name.startswith(DEPOSIT_RETURN_PREFIXES)


def _is_separator(line: str) -> bool:
    return line.startswith(SEPARATOR_PREFIXES)
