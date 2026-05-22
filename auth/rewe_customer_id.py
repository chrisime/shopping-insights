"""Utilities for resolving and caching the REWE customerId used by the ZIP endpoint."""

import re
from pathlib import Path
from typing import Optional

from pyarrow.lib import UUID

import requests

from config import ReweConfig

from .shared_file_auth import read_utf8_text_file


CUSTOMER_ID_PATTERN = re.compile(
    r"(?:customerId|customerUUID)\b(?:\"?\s*[:=]\s*\"?)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
    re.IGNORECASE,
)
CACHE_FILE_NAME = "customer_id.txt"


def resolve_rewe_customer_id(
    customer_id: Optional[str],
    session: Optional[requests.Session],
    cookies_file: Optional[str],
    output_dir: Path,
) -> Optional[str]:
    """Resolve a usable REWE customerId from explicit input, session, local files or cache."""
    if customer_id:
        return _normalize_customer_id(customer_id)

    session_customer_id = _read_customer_id_from_session(session)
    if session_customer_id:
        return session_customer_id

    file_customer_id = _read_customer_id_from_file(Path(cookies_file) if cookies_file else None)
    if file_customer_id:
        return file_customer_id

    return _load_cached_customer_id(output_dir)


def _read_customer_id_from_session(session: Optional[requests.Session]) -> Optional[str]:
    """Read the current REWE customer UUID from the authenticated coupon wallet endpoint."""
    if session is None:
        return None

    response = None
    try:
        response = session.get(
            ReweConfig.get_coupon_wallet_url(),
            timeout=ReweConfig.DEFAULT_TIMEOUT,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": ReweConfig.get_mydata_receipts_url(),
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        if response.status_code != 200:
            return None

        return extract_rewe_customer_id_from_text(response.text)
    except requests.exceptions.RequestException:
        return None
    finally:
        if response is not None:
            response.close()


def cache_customer_id(customer_id: str, output_dir: Path) -> None:
    """Persist the last successful REWE customerId for future runs."""
    normalized = _normalize_customer_id(customer_id)
    if not normalized:
        return

    cache_path = output_dir / CACHE_FILE_NAME
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(normalized, encoding="utf-8")


def _load_cached_customer_id(output_dir: Path) -> Optional[str]:
    """Load a previously cached REWE customerId if present."""
    cache_path = output_dir / CACHE_FILE_NAME
    if not cache_path.exists():
        return None

    raw_text = read_utf8_text_file(str(cache_path)).strip()
    return _normalize_customer_id(raw_text) or extract_rewe_customer_id_from_text(raw_text)


def _read_customer_id_from_file(file_path: Optional[Path]) -> Optional[str]:
    """Search a file for a raw UUID or a customerId key/value occurrence."""
    if file_path is None or not file_path.exists():
        return None

    raw_text = read_utf8_text_file(str(file_path)).strip()
    return _normalize_customer_id(raw_text) or extract_rewe_customer_id_from_text(raw_text)


def extract_rewe_customer_id_from_text(raw_text: str) -> Optional[str]:
    """Search raw text for a customer UUID in known REWE response formats."""
    match = CUSTOMER_ID_PATTERN.search(raw_text)
    if match:
        return _normalize_customer_id(match.group(1))
    return None


def _normalize_customer_id(value: str) -> Optional[str]:
    """Validate and normalize a customerId UUID."""
    try:
        return str(UUID(value.strip()))
    except (AttributeError, TypeError, ValueError):
        return None


