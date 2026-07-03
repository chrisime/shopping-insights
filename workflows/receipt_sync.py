"""Generic helpers shared by retailer-specific receipt workflows."""

import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from storage import add_receipt_to_json, sort_receipts_by_date, upsert_receipts

from .progress_display import ProgressState, ReceiptProgressDisplay


ReceiptFetcher = Callable[[str], Optional[Dict[str, Any]]]


def filter_new_receipt_ids(
    receipt_ids: Sequence[str], existing_ids: Iterable[str]
) -> List[str]:
    """Return only receipt IDs that are not already stored."""
    existing_id_set = set(existing_ids)
    return [receipt_id for receipt_id in receipt_ids if receipt_id not in existing_id_set]


def process_receipt_ids_with_progress(
    receipt_ids: Sequence[str],
    fetch_receipt_data: ReceiptFetcher,
    retailer: str,
    request_delay: float = 0.0,
) -> Tuple[int, int, int, int]:
    """Fetch, persist and track receipt processing progress."""
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_items = 0
    current_receipt = "-"
    total_receipts = len(receipt_ids)

    progress = ReceiptProgressDisplay()
    progress.render(
        ProgressState(
            current=0,
            total=total_receipts,
            added=processed_count,
            skipped=skipped_count,
            errors=error_count,
            items=total_items,
            current_receipt=current_receipt,
        )
    )

    for index, receipt_id in enumerate(receipt_ids, 1):
        current_receipt = receipt_id
        progress.render(
            ProgressState(
                current=index - 1,
                total=total_receipts,
                added=processed_count,
                skipped=skipped_count,
                errors=error_count,
                items=total_items,
                current_receipt=current_receipt,
            )
        )

        receipt_data = fetch_receipt_data(receipt_id)
        if receipt_data and receipt_data.get("items"):
            add_receipt_to_json(receipt_data, verbose=False, retailer=retailer)
            processed_count += 1
            total_items += len(receipt_data["items"])
        else:
            skipped_count += 1
            error_count += 1

        progress.render(
            ProgressState(
                current=index,
                total=total_receipts,
                added=processed_count,
                skipped=skipped_count,
                errors=error_count,
                items=total_items,
                current_receipt=current_receipt,
            )
        )

        if request_delay > 0:
            time.sleep(request_delay)

    progress.close()
    return processed_count, skipped_count, error_count, total_items


def persist_receipts(
    receipts: Sequence[Dict[str, Any]],
    retailer: str,
    file_path: Optional[str] = None,
) -> Tuple[int, int, int]:
    """Upsert and sort receipt data using the shared storage layer."""
    created_count, updated_count, _ = upsert_receipts(
        receipts,
        file_path=file_path,
        retailer=retailer,
    )
    total_receipts = sort_receipts_by_date(file_path=file_path, retailer=retailer)
    return created_count, updated_count, total_receipts


def finalize_receipts_file(
    retailer: str,
    processed_count: int,
    existing_count: int,
    file_path: Optional[str] = None,
) -> int:
    """Sort the receipts file when new receipts were added."""
    if processed_count <= 0:
        return existing_count
    return sort_receipts_by_date(file_path=file_path, retailer=retailer)

