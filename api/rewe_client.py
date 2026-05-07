"""Minimal REWE API client for downloading eBon ZIP archives."""

import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import requests

from config import ReweConfig


RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _build_receipts_zip_url(customer_id: Optional[str] = None) -> str:
    """Build the absolute ZIP download URL for a REWE customer."""
    if not customer_id:
        return ReweConfig.get_receipts_zip_url()

    query = urlencode({"customerId": customer_id})
    return f"{ReweConfig.get_receipts_zip_url()}?{query}"


def test_rewe_session(
    session: requests.Session,
    customer_id: Optional[str] = None,
) -> bool:
    """Perform a lightweight session test against the ZIP endpoint.

    The request is streamed and immediately closed to avoid downloading the full body.
    """
    try:
        response = session.get(
            _build_receipts_zip_url(customer_id),
            timeout=ReweConfig.DEFAULT_TIMEOUT,
            stream=True,
        )
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            response.close()
            return "application/zip" in content_type

        response.close()
        return False
    except requests.exceptions.RequestException:
        return False


def download_receipts_zip(
    session: requests.Session,
    customer_id: Optional[str],
    output_path: Path,
) -> Optional[Path]:
    """Download the REWE receipts ZIP archive to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    url = _build_receipts_zip_url(customer_id)

    last_exception: Optional[Exception] = None
    for attempt in range(1, ReweConfig.MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                timeout=ReweConfig.DEFAULT_TIMEOUT,
                stream=True,
            )

            if response.status_code == 200:
                with open(output_path, "wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            handle.write(chunk)
                response.close()
                return output_path

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < ReweConfig.MAX_RETRIES:
                response.close()
                wait_seconds = ReweConfig.RETRY_BACKOFF_SECONDS ** attempt
                time.sleep(wait_seconds)
                continue

            response.close()
            return None
        except requests.exceptions.RequestException as exc:
            last_exception = exc
            if attempt >= ReweConfig.MAX_RETRIES:
                break
            wait_seconds = ReweConfig.RETRY_BACKOFF_SECONDS ** attempt
            time.sleep(wait_seconds)

    return None


test_rewe_session.__test__ = False
