"""Rossmann anybill App API v4 client for digital receipt retrieval.

Rossmann receipts are served by anybill (white-label). This module talks to
the publicly documented anybill App API v4 with the anybill Bearer token
minted via :mod:`auth.rossmann_auth`. On 401 the client re-mints a token via
the provided refresher and retries once.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import requests

from config import RossmannConfig


def _request_with_retry(
    session: requests.Session,
    url: str,
    *,
    token_refresher: Callable[[], str | None] | None = None,
    params: dict[str, Any] | None = None,
    stream: bool = False,
) -> requests.Response | None:
    """GET ``url`` with retry/backoff on 429/5xx and one 401 token refresh."""
    for attempt in range(1, RossmannConfig.MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=RossmannConfig.DEFAULT_TIMEOUT,
                stream=stream,
            )

            if response.status_code == 401 and token_refresher is not None and attempt == 1:
                new_token = token_refresher()
                if new_token:
                    session.headers["Authorization"] = (
                        f"{RossmannConfig.ANYBILL_TOKEN_PREFIX}{new_token}"
                    )
                    continue

            if response.ok:
                return response

            if (
                response.status_code in RossmannConfig.RETRYABLE_STATUS_CODES
                and attempt < RossmannConfig.MAX_RETRIES
            ):
                time.sleep(RossmannConfig.RETRY_BACKOFF_SECONDS**attempt)
                continue

            return response

        except requests.exceptions.RequestException:
            if attempt >= RossmannConfig.MAX_RETRIES:
                return None
            time.sleep(RossmannConfig.RETRY_BACKOFF_SECONDS**attempt)

    return None


def _parse_continuation_token(response: requests.Response) -> str | None:
    """Read the ``ContinuationToken`` response header used for pagination."""
    value = response.headers.get("ContinuationToken")
    return value if value else None


def fetch_receipts(
    session: requests.Session,
    take: int = RossmannConfig.DEFAULT_PAGE_SIZE,
    continuation_token: str | None = None,
    token_refresher: Callable[[], str | None] | None = None,
) -> tuple[list[dict] | None, str | None]:
    """Fetch one page of anybill receipts.

    Returns ``(receipts, continuation_token)`` where the token is ``None``
    when the end of pagination is reached.
    """
    params: dict[str, Any] = {"take": take, "orderBy": "Date", "orderByDirection": "Descending"}
    if continuation_token:
        params["continuationToken"] = continuation_token

    response = _request_with_retry(
        session,
        RossmannConfig.get_anybill_receipts_url(),
        params=params,
        token_refresher=token_refresher,
    )
    if response is None or not response.ok:
        return None, None

    try:
        data = response.json()
    except ValueError:
        return None, None

    if not isinstance(data, list):
        return None, None

    receipts = [item for item in data if isinstance(item, dict)]
    return receipts, _parse_continuation_token(response)


def collect_rossmann_receipts(
    session: requests.Session,
    token_refresher: Callable[[], str | None] | None = None,
) -> list[dict] | None:
    """Fetch all pages of anybill receipts until the continuation token ends."""
    receipts: list[dict] = []
    continuation_token: str | None = None
    seen_tokens: set[str] = set()

    while True:
        page, continuation_token = fetch_receipts(
            session,
            take=100,
            continuation_token=continuation_token,
            token_refresher=token_refresher,
        )
        if page is None:
            return None
        receipts.extend(page)
        if not continuation_token:
            break
        if continuation_token in seen_tokens:
            return None
        seen_tokens.add(continuation_token)
        if RossmannConfig.REQUEST_DELAY > 0:
            time.sleep(RossmannConfig.REQUEST_DELAY)

    return receipts


def fetch_receipt_detail(
    session: requests.Session,
    receipt_id: str,
    token_refresher: Callable[[], str | None] | None = None,
) -> dict | None:
    """Fetch the detail JSON for one anybill receipt."""
    response = _request_with_retry(
        session,
        RossmannConfig.get_anybill_receipt_detail_url(receipt_id),
        token_refresher=token_refresher,
    )
    if response is None or not response.ok:
        return None

    try:
        data = response.json()
        return data if isinstance(data, dict) else None
    except ValueError:
        return None


def download_receipt_pdf(
    session: requests.Session,
    receipt_id: str,
    output_path: Path,
    token_refresher: Callable[[], str | None] | None = None,
) -> Path | None:
    """Download the anybill receipt PDF to ``output_path``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = _request_with_retry(
        session,
        RossmannConfig.get_anybill_receipt_pdf_url(receipt_id),
        stream=True,
        token_refresher=token_refresher,
    )
    if response is None or not response.ok:
        return None

    with open(output_path, "wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                handle.write(chunk)
    return output_path


def test_rossmann_session(
    session: requests.Session,
    token_refresher: Callable[[], str | None] | None = None,
) -> bool:
    """Perform a lightweight session test against the anybill receipt list."""
    page, _ = fetch_receipts(
        session,
        take=1,
        token_refresher=token_refresher,
    )
    return page is not None


test_rossmann_session.__test__ = False  # type: ignore[attr-defined]
