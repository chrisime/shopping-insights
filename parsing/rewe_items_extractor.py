"""Extract REWE receipt items, discounts and deposit returns from PDF lines."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, List, Optional

from shared.receipt_schema import build_receipt_item
from .rewe_parser_common import to_rewe_float


ITEM_LINE_RE = re.compile(r"^(?P<name>.+?)\s+(?P<amount>-?\d+,\d{2})\s+(?P<tax>[A-Z])(?:\s+\*)?$")
QUANTITY_LINE_RE = re.compile(
    r"^(?P<quantity>-?\d+(?:,\d+)?)\s*(?P<unit>Stk|kg)\s*x\s*"
    r"(?P<unit_price>-?\d+,\d{2})(?:\s*EUR/kg)?$"
)
HANDEINGABE_RE = re.compile(
    r"Handeingabe\s+E-Bon\s+(?P<weight>\d+[,.]\d+)\s+kg"
)
SUM_RE = re.compile(r"SUMME EUR\s+(?P<amount>\d+,\d{2})")
SEPARATOR_PREFIXES = ("-----", "=====", "*****")
DEPOSIT_RETURN_PREFIXES = ("LEERG.", "LEERGUT")


@dataclass
class _PendingItem:
    """Mutable intermediate representation of a parsed item before commit."""

    name: str
    total_amount: float
    quantity: Any = 1
    unit: str = "stk"
    unit_price: Optional[str] = None


@dataclass(frozen=True)
class ReweItemsExtractionResult:
    """Structured result for parsed REWE items and savings aggregates."""

    items: List[Dict[str, Any]]
    saved_amount: float
    saved_deposit: float


@dataclass(frozen=True)
class _CommitResult:
    """Pure return value from committing a pending item – no side effects."""

    item: Optional[Dict[str, Any]] = None
    saved_amount: float = 0.0
    saved_deposit: float = 0.0


def extract_rewe_receipt_items(lines: List[str]) -> ReweItemsExtractionResult:
    """Extract normalized items and aggregate discount/deposit amounts.

    Uses the pending-item pattern: an article line opens a pending item,
    subsequent modifier lines (quantity, weight, Handeingabe) update it,
    and the next article line or end-of-block commits it.
    """
    items: List[Dict[str, Any]] = []
    saved_amount = 0.0
    saved_pfand = 0.0
    pending: Optional[_PendingItem] = None

    body_lines = _extract_receipt_body_lines(lines)

    for line in body_lines:
        # --- Modifier lines update the pending item ---

        # Quantity/weight line: "2 Stk x 0,39" or "0,552 kg x 3,99 EUR/kg"
        quantity_match = QUANTITY_LINE_RE.match(line)
        if quantity_match and pending is not None:
            pending.quantity = quantity_match.group("quantity")
            pending.unit = quantity_match.group("unit").lower()
            pending.unit_price = quantity_match.group("unit_price").lstrip("-")
            continue

        # Handeingabe line: "Handeingabe E-Bon 0,422 kg"
        handeingabe_match = HANDEINGABE_RE.search(line)
        if handeingabe_match and pending is not None:
            weight = to_rewe_float(handeingabe_match.group("weight"))
            if weight > 0:
                pending.unit_price = str(round(pending.total_amount / weight, 2)).replace(".", ",")
                pending.quantity = handeingabe_match.group("weight")
                pending.unit = "kg"
            continue

        # --- Article line: commit previous pending, open new one ---
        item_match = ITEM_LINE_RE.match(line)
        if item_match:
            # Commit previous pending item
            result = _commit_pending(pending)
            saved_amount += result.saved_amount
            saved_pfand += result.saved_deposit
            if result.item is not None:
                items.append(result.item)

            # Open new pending item
            name = _normalize_item_name(item_match.group("name"))
            amount_text = item_match.group("amount")
            total_amount = to_rewe_float(amount_text)
            pending = _PendingItem(
                name=name,
                total_amount=total_amount,
                unit_price=amount_text.lstrip("-"),
            )
            continue

        # Non-matching lines: ignore (pending stays open for further modifiers)

    # Commit last pending item
    result = _commit_pending(pending)
    saved_amount += result.saved_amount
    saved_pfand += result.saved_deposit
    if result.item is not None:
        items.append(result.item)

    return ReweItemsExtractionResult(
        items=items,
        saved_amount=saved_amount,
        saved_deposit=saved_pfand,
    )


def _commit_pending(pending: Optional[_PendingItem]) -> _CommitResult:
    """Convert a pending item into a pure result without side effects."""
    if pending is None:
        return _CommitResult()

    if pending.total_amount < 0:
        amount = abs(pending.total_amount)
        if _is_deposit_return(pending.name):
            return _CommitResult(saved_deposit=amount)
        return _CommitResult(saved_amount=amount)

    item = build_receipt_item(
        name=pending.name,
        price=pending.unit_price or str(pending.total_amount).replace(".", ","),
        quantity=pending.quantity,
        unit=pending.unit,
    )
    return _CommitResult(item=item)


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
        current_line = lines[index]
        if current_line.startswith(SEPARATOR_PREFIXES):
            body_end = index
            break

    return lines[start_index:body_end]


def _normalize_item_name(name: str) -> str:
    normalized = re.sub(r"\s+", " ", name).strip()
    if normalized.startswith("PFAND ") and " EUR" in normalized:
        return "PFAND"
    return normalized


def _is_deposit_return(name: str) -> bool:
    return name.upper().startswith(DEPOSIT_RETURN_PREFIXES)
