"""API client module for shopping analyzer."""

from .lidl_client import (
    collect_lidl_receipt_ids,
    get_lidl_ticket,
    get_tickets_page,
    test_lidl_session,
)
from .rewe_client import (
    RETRYABLE_STATUS_CODES,
    download_receipts_zip,
    test_rewe_session,
)

__all__ = [
    "collect_lidl_receipt_ids",
    "get_tickets_page",
    "get_lidl_ticket",
    "test_lidl_session",
    "RETRYABLE_STATUS_CODES",
    "download_receipts_zip",
    "test_rewe_session",
]
