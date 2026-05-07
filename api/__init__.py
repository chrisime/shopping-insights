"""API client module for shopping analyzer."""

from .lidl_client import (
    get_lidl_ticket,
    get_tickets_page,
    test_lidl_session,
)
from .rewe_client import (
    download_receipts_zip,
    test_rewe_session,
)

__all__ = [
    "get_tickets_page",
    "get_lidl_ticket",
    "test_lidl_session",
    "download_receipts_zip",
    "test_rewe_session",
]
