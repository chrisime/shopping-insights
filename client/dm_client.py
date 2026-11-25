"""dm API client for purchase history and eBon retrieval.

The dm backend (reverse-engineered from ``account.dm.de/purchases``) exposes a
paginated purchase-history list plus per-eBon detail and PDF download. All
requests use a fresh bearer token from :mod:`auth.dm_auth`; on 401 the client
re-mints a token via the provided refresher and retries once.
"""

from __future__ import annotations

import time
from datetime import date
from pathlib import Path
from typing import Any, Callable

import requests

from config import DmConfig
from shared.receipt_dates import api_purchase_date


def _request_with_retry(
    session: requests.Session,
    url: str,
    *,
    token_refresher: Callable[[], str | None] | None = None,
    params: dict[str, Any] | None = None,
    stream: bool = False,
) -> requests.Response | None:
    """GET ``url`` with retry/backoff on 429/5xx and one 401 token refresh."""
    for attempt in range(1, DmConfig.MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=DmConfig.DEFAULT_TIMEOUT,
                stream=stream,
            )

            if response.status_code == 401 and token_refresher is not None and attempt == 1:
                new_token = token_refresher()
                if new_token:
                    session.headers["Authorization"] = f"Bearer {new_token}"
                    continue

            if response.ok:
                return response

            if (
                response.status_code in DmConfig.RETRYABLE_STATUS_CODES
                and attempt < DmConfig.MAX_RETRIES
            ):
                time.sleep(DmConfig.RETRY_BACKOFF_SECONDS**attempt)
                continue

            return response

        except requests.exceptions.RequestException:
            if attempt >= DmConfig.MAX_RETRIES:
                return None
            time.sleep(DmConfig.RETRY_BACKOFF_SECONDS**attempt)

    return None


def fetch_purchase_history(
    session: requests.Session,
    until_date_time_placed: str | None = None,
    size: int = DmConfig.DEFAULT_PAGE_SIZE,
    token_refresher: Callable[[], str | None] | None = None,
) -> dict | None:
    """Fetch one page of the dm purchase history.

    Args:
        session: dm API session carrying the bearer token.
        until_date_time_placed: cursor for the next (older) page.
        size: page size (max 20 per the dm frontend).
        token_refresher: callable minting a fresh token on 401.

    Returns:
        The parsed JSON response or ``None`` on a failed request.
    """
    params: dict[str, object] = {"size": size}
    if until_date_time_placed:
        params["untilDateTimePlaced"] = until_date_time_placed

    response = _request_with_retry(
        session,
        DmConfig.get_purchase_history_url(),
        params=params,
        token_refresher=token_refresher,
    )
    if response is None or not response.ok:
        return None

    try:
        return response.json()
    except ValueError:
        return None


def collect_dm_purchases(
    session: requests.Session,
    token_refresher: Callable[[], str | None] | None = None,
    *,
    purchased_since: date | None = None,
) -> list[dict]:
    """Collect eligible purchases from newest-to-oldest history pages."""
    purchases: list[dict] = []
    until_date_time_placed: str | None = None

    while True:
        data = fetch_purchase_history(
            session,
            until_date_time_placed=until_date_time_placed,
            token_refresher=token_refresher,
        )
        if data is None:
            break

        items = data.get("purchaseHistoryItems") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            purchase_date = api_purchase_date(item.get("dateTimePlaced"))
            if purchased_since is None or purchase_date is None or purchase_date >= purchased_since:
                purchases.append(item)

        if not data.get("hasMoreElements") or not items:
            break

        last_item = items[-1]
        raw_cursor = last_item.get("dateTimePlaced") if isinstance(last_item, dict) else None
        cursor_date = api_purchase_date(raw_cursor)
        if purchased_since is not None and cursor_date is not None and cursor_date < purchased_since:
            break

        until_date_time_placed = str(raw_cursor) if raw_cursor else None
        if not until_date_time_placed:
            break

        if DmConfig.REQUEST_DELAY > 0:
            time.sleep(DmConfig.REQUEST_DELAY)

    return purchases


def fetch_ebon_detail(
    session: requests.Session,
    ebon_id: str,
    token_refresher: Callable[[], str | None] | None = None,
) -> dict | None:
    """Fetch the detail JSON for one dm eBon."""
    response = _request_with_retry(
        session,
        DmConfig.get_ebon_detail_url(ebon_id),
        token_refresher=token_refresher,
    )
    if response is None or not response.ok:
        return None

    try:
        data = response.json()
        return data if isinstance(data, dict) else None
    except ValueError:
        return None


def download_ebon_pdf(
    session: requests.Session,
    ebon_id: str,
    output_path: Path,
    token_refresher: Callable[[], str | None] | None = None,
) -> Path | None:
    """Download the dm eBon PDF to ``output_path`` and return it on success."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = _request_with_retry(
        session,
        DmConfig.get_ebon_download_url(ebon_id),
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


def test_dm_session(
    session: requests.Session,
    token_refresher: Callable[[], str | None] | None = None,
) -> bool:
    """Perform a lightweight session test against the purchase-history API."""
    data = fetch_purchase_history(
        session,
        size=1,
        token_refresher=token_refresher,
    )
    return data is not None


test_dm_session.__test__ = False  # type: ignore[attr-defined]