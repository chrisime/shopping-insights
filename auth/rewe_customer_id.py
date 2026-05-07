"""Utilities for resolving and caching the REWE customerId used by the ZIP endpoint."""

import os
import re
from pathlib import Path
from typing import Optional

import requests

from config import ReweConfig

from .shared_file_auth import read_utf8_text_file


CUSTOMER_ID_PATTERN = re.compile(
    r"(?:customerId|customerUUID)\b(?:\"?\s*[:=]\s*\"?)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
    re.IGNORECASE,
)
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
CACHE_FILE_NAME = "customer_id.txt"


def resolve_rewe_customer_id(
    customer_id: Optional[str],
    session: Optional[requests.Session],
    cookies_file: Optional[str],
    output_dir: str,
) -> Optional[str]:
    """Resolve a usable REWE customerId from explicit input, session, local files or cache."""
    if customer_id:
        normalized = _normalize_customer_id(customer_id)
        return normalized

    session_customer_id = fetch_customer_id_from_session(session)
    if session_customer_id:
        return session_customer_id

    extracted_from_file = _extract_customer_id_from_file(cookies_file)
    if extracted_from_file:
        return extracted_from_file

    cached_customer_id = load_cached_customer_id(output_dir)
    if cached_customer_id:
        return cached_customer_id

    return None


def fetch_customer_id_from_session(session: Optional[requests.Session]) -> Optional[str]:
    """Read the current REWE customer UUID from the authenticated coupon wallet endpoint."""
    if session is None:
        return None

    try:
        response = session.get(
            ReweConfig.get_coupon_wallet_url(),
            timeout=ReweConfig.DEFAULT_TIMEOUT,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": f"{ReweConfig.BASE_URL}/shop/mydata/meine-einkaeufe/im-markt",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        response.close()
        return None

    customer_id = extract_rewe_customer_id_from_text(response.text)
    response.close()
    return customer_id


def cache_customer_id(customer_id: str, output_dir: str) -> None:
    """Persist the last successful REWE customerId for future runs."""
    normalized = _normalize_customer_id(customer_id)
    if not normalized:
        return

    cache_path = _get_cache_path(output_dir)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(normalized, encoding="utf-8")


def load_cached_customer_id(output_dir: str) -> Optional[str]:
    """Load a previously cached REWE customerId if present."""
    cache_path = _get_cache_path(output_dir)
    if not cache_path.exists():
        return None

    return _normalize_customer_id(cache_path.read_text(encoding="utf-8").strip())


def _extract_customer_id_from_file(file_path: Optional[str]) -> Optional[str]:
    """Search a file for a customerId query parameter or key/value occurrence."""
    if not file_path or not os.path.exists(file_path):
        return None

    raw_text = read_utf8_text_file(file_path)
    return extract_rewe_customer_id_from_text(raw_text)


def extract_rewe_customer_id_from_text(raw_text: str) -> Optional[str]:
    """Search raw text for a customer UUID in known REWE response formats."""
    match = CUSTOMER_ID_PATTERN.search(raw_text)
    if match:
        return _normalize_customer_id(match.group(1))
    return None


def _normalize_customer_id(value: str) -> Optional[str]:
    """Validate and normalize a customerId UUID."""
    stripped = value.strip()
    if UUID_PATTERN.match(stripped):
        return stripped.lower()
    return None


def _get_cache_path(output_dir: str) -> Path:
    """Return the cache file path for the customerId."""
    return Path(output_dir) / CACHE_FILE_NAME

