"""JSON-backed receipt store and helper functions."""

from __future__ import annotations

from datetime import datetime
import json
import os
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from config import LidlConfig, ReweConfig
from result_types import PersistResult, ReceiptStoreSnapshot
from shared.ports import ReceiptStore
from shared.receipt_schema import normalize_receipt_schema


RECEIPTS_FILES_BY_RETAILER = {
    "lidl": LidlConfig.RECEIPTS_JSON_FILE,
    "rewe": ReweConfig.RECEIPTS_JSON_FILE,
}


DATE_FORMATS = (
    "%d.%m.%Y %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y",
    "%Y.%m.%d %H:%M",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d",
)


def _resolve_receipts_file_path(
    file_path: Optional[str] = None,
    retailer: Optional[str] = None,
) -> str:
    """Resolve the JSON file path used for receipt persistence."""
    if file_path:
        return file_path

    if retailer:
        normalized_retailer = retailer.lower()
        if normalized_retailer not in RECEIPTS_FILES_BY_RETAILER:
            raise ValueError(f"Unbekannter Händler für Receipt-Storage: {retailer}")
        return RECEIPTS_FILES_BY_RETAILER[normalized_retailer]

    return LidlConfig.RECEIPTS_JSON_FILE


def _load_existing_receipts(
    file_path: Optional[str] = None,
    retailer: Optional[str] = None,
) -> tuple[set[str], list[Dict[str, Any]], str]:
    """Load existing raw receipts from the resolved JSON file."""
    receipts_file = _resolve_receipts_file_path(file_path=file_path, retailer=retailer)

    if not os.path.exists(receipts_file):
        return set(), [], receipts_file

    try:
        with open(receipts_file, "r", encoding="utf-8") as file:
            receipts = json.load(file)

        if not isinstance(receipts, list):
            return set(), [], receipts_file

        existing_ids = set()
        for receipt in receipts:
            if "id" in receipt:
                existing_ids.add(receipt["id"])
            elif "url" in receipt:
                existing_ids.add(receipt["url"])
        return existing_ids, receipts, receipts_file
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Error loading existing receipts: {e}")
        return set(), [], receipts_file


def _save_receipts_to_json(
    receipts: list[Dict[str, Any]],
    file_path: Optional[str] = None,
    retailer: Optional[str] = None,
) -> None:
    """Save normalized receipts to the resolved JSON file."""
    receipts_file = _resolve_receipts_file_path(file_path=file_path, retailer=retailer)

    with open(receipts_file, "w", encoding="utf-8") as file:
        json.dump(receipts, file, ensure_ascii=False, indent=2)


def upsert_receipts(
    receipts_data: Iterable[Dict[str, Any]],
    file_path: Optional[str] = None,
    retailer: Optional[str] = None,
) -> Tuple[int, int, int]:
    """Insert or update multiple receipts in a single storage pass.

    Returns:
        tuple: (created_count, updated_count, total_count_after_merge)
    """
    _, existing_receipts, _ = _load_existing_receipts(
        file_path=file_path,
        retailer=retailer,
    )
    existing_receipts = [
        normalize_receipt_schema(receipt, retailer=retailer)
        for receipt in existing_receipts
    ]
    receipts_by_id = {
        (receipt.get("id") or receipt.get("url")): receipt
        for receipt in existing_receipts
        if receipt.get("id") or receipt.get("url")
    }

    created_count = 0
    updated_count = 0

    for receipt_data in receipts_data:
        normalized_receipt_data = normalize_receipt_schema(receipt_data, retailer=retailer)
        receipt_id = normalized_receipt_data.get("id") or normalized_receipt_data.get("url")
        if not receipt_id:
            continue

        existing_receipt = receipts_by_id.get(receipt_id)
        if existing_receipt is None:
            receipts_by_id[receipt_id] = normalized_receipt_data
            created_count += 1
            continue

        if existing_receipt != normalized_receipt_data:
            receipts_by_id[receipt_id] = normalized_receipt_data
            updated_count += 1

    merged_receipts = list(receipts_by_id.values())
    _save_receipts_to_json(
        merged_receipts,
        file_path=file_path,
        retailer=retailer,
    )
    return created_count, updated_count, len(merged_receipts)


def sort_receipts_by_date(
    file_path: Optional[str] = None,
    retailer: Optional[str] = None,
) -> int:
    """Sort all receipts in the JSON file by date (newest first)."""
    _, receipts, _ = _load_existing_receipts(file_path=file_path, retailer=retailer)
    receipts = [
        normalize_receipt_schema(receipt, retailer=retailer)
        for receipt in receipts
    ]

    def get_date_key(receipt):
        date_str = receipt.get("purchase_date")
        if not date_str:
            return datetime.min
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        return datetime.min

    sorted_receipts = sorted(receipts, key=get_date_key, reverse=True)
    _save_receipts_to_json(
        sorted_receipts,
        file_path=file_path,
        retailer=retailer,
    )
    return len(sorted_receipts)



class JsonReceiptStore(ReceiptStore):
    """JSON-backed receipt store used by the current workflows."""

    def load_receipts_snapshot(
        self,
        retailer: str,
        file_path: Optional[str] = None,
    ) -> ReceiptStoreSnapshot:
        existing_ids, receipts, receipts_file = _load_existing_receipts(
            file_path=file_path,
            retailer=retailer,
        )
        return ReceiptStoreSnapshot(
            existing_ids=existing_ids,
            receipts=receipts,
            receipts_file=receipts_file,
        )

    def persist_receipts(
        self,
        receipts: Sequence[Dict[str, Any]],
        retailer: str,
        file_path: Optional[str] = None,
    ) -> PersistResult:
        created_count, updated_count, _ = upsert_receipts(
            receipts,
            file_path=file_path,
            retailer=retailer,
        )
        total_receipts = sort_receipts_by_date(file_path=file_path, retailer=retailer)
        return PersistResult(
            created_count=created_count,
            updated_count=updated_count,
            total_receipts=total_receipts,
        )



