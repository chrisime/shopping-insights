"""JSON receipt repository helpers used by legacy workflow paths."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from config.retailer_profiles import resolve_retailer_receipts_json_file
from shared.receipt_dates import parse_purchase_date
from shared.receipt_schema import normalize_receipt_schema


def add_receipt_to_json(
    receipt_data: Dict[str, Any],
    verbose: bool = False,
    retailer: str | None = None,
    file_path: str | None = None,
) -> Tuple[int, int, int]:
    """Insert or update one receipt in the JSON repository."""
    created_count, updated_count, total_count = upsert_receipts(
        [receipt_data],
        file_path=file_path,
        retailer=retailer,
    )
    sort_receipts_by_date(file_path=file_path, retailer=retailer)
    return created_count, updated_count, total_count


def upsert_receipts(
    receipts: Sequence[Dict[str, Any]],
    file_path: str | None = None,
    retailer: str | None = None,
) -> Tuple[int, int, int]:
    """Upsert normalized receipts into the retailer JSON file."""
    target_path = _resolve_receipts_path(file_path=file_path, retailer=retailer)
    existing_receipts = _load_receipts(target_path)
    receipt_index = _index_receipts(existing_receipts)

    created_count = 0
    updated_count = 0

    for receipt in receipts:
        normalized_receipt = normalize_receipt_schema(receipt, retailer=retailer)
        if str(retailer or "").strip().lower() == "rewe":
            if normalized_receipt.get("rewe_bonus_amount") is None:
                normalized_receipt["rewe_bonus_amount"] = 0.0
            if normalized_receipt.get("rewe_bonus_amount_saved") is None:
                normalized_receipt["rewe_bonus_amount_saved"] = 0.0
        receipt_key = _receipt_key(normalized_receipt)
        if not receipt_key:
            continue

        normalized_receipt["id"] = receipt_key
        if receipt_key in receipt_index:
            existing_receipts[receipt_index[receipt_key]] = normalized_receipt
            updated_count += 1
        else:
            receipt_index[receipt_key] = len(existing_receipts)
            existing_receipts.append(normalized_receipt)
            created_count += 1

    _write_receipts(target_path, existing_receipts)
    return created_count, updated_count, len(existing_receipts)


def sort_receipts_by_date(file_path: str | None = None, retailer: str | None = None) -> int:
    """Sort JSON receipts descending by purchase date and return the total count."""
    target_path = _resolve_receipts_path(file_path=file_path, retailer=retailer)
    receipts = _load_receipts(target_path)
    receipts.sort(key=_purchase_date_sort_key, reverse=True)
    _write_receipts(target_path, receipts)
    return len(receipts)


def _resolve_receipts_path(file_path: str | None, retailer: str | None) -> Path:
    return Path(resolve_retailer_receipts_json_file(retailer, file_path))


def _load_receipts(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    return [receipt for receipt in data if isinstance(receipt, dict)]


def _write_receipts(path: Path, receipts: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(receipts), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _index_receipts(receipts: Sequence[Dict[str, Any]]) -> dict[str, int]:
    index: dict[str, int] = {}
    for position, receipt in enumerate(receipts):
        key = _receipt_key(receipt)
        if key:
            index[key] = position
    return index


def _receipt_key(receipt: Dict[str, Any]) -> str:
    return str(receipt.get("id") or receipt.get("url") or "").strip()


def _purchase_date_sort_key(receipt: Dict[str, Any]) -> datetime:
    parsed_date = _parse_legacy_purchase_date(receipt.get("purchase_date"))
    if parsed_date is None:
        return datetime.min
    return parsed_date


def _parse_legacy_purchase_date(value: Any) -> datetime | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    for fmt in (
        "%Y.%m.%d",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    parsed_date = parse_purchase_date(text)
    if parsed_date is not None:
        return parsed_date

    return None
