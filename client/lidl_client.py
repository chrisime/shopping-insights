"""Lidl API client for fetching receipt data."""

import time
from typing import List, Optional, Tuple

import requests
import simplejson

from config import LidlConfig
from shared.lidl_ticket_dto import LidlTicketDTO, LidlTicketsPageDTO


def _request_with_retry(
    session: requests.Session,
    url: str,
    **kwargs: object,
) -> Optional[requests.Response]:
    for attempt in range(1, LidlConfig.MAX_RETRIES + 1):
        try:
            response = session.get(url, **kwargs)

            if response.ok:
                return response

            if (
                response.status_code in LidlConfig.RETRYABLE_STATUS_CODES
                and attempt < LidlConfig.MAX_RETRIES
            ):
                wait = LidlConfig.RETRY_BACKOFF_SECONDS**attempt
                time.sleep(wait)
                continue

            return response

        except requests.exceptions.RequestException:
            if attempt >= LidlConfig.MAX_RETRIES:
                return None
            wait = LidlConfig.RETRY_BACKOFF_SECONDS**attempt
            time.sleep(wait)

    return None


def get_tickets_page(
    session: requests.Session, page: int = 1
) -> Optional[LidlTicketsPageDTO]:
    """
    Fetch tickets for a specific page using the API.

    Args:
        session: requests.Session with authentication
        page: Page number to fetch

    Returns:
        LidlTicketsPageDTO: Structured pagination response with typed ticket previews, or None if error
    """
    url = f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page={page}"
    response = _request_with_retry(session, url, timeout=LidlConfig.DEFAULT_TIMEOUT)
    if response is None:
        return None

    try:
        data = response.json()
    except simplejson.JSONDecodeError:
        return None

    if isinstance(data, list):
        return LidlTicketsPageDTO.from_api_response(
            {
                "items": data,
                "page": page,
                "size": len(data),
                "totalCount": len(data),
            },
            page=page,
        )
    elif isinstance(data, dict):
        return LidlTicketsPageDTO.from_api_response(data, page=page)

    return None


def get_lidl_ticket(session: requests.Session, receipt_id: str) -> LidlTicketDTO:
    """
    Fetch the Lidl ticket for a specific receipt and return it as a structured DTO.

    Args:
        session: requests.Session with authentication
        receipt_id: Receipt ID to fetch

    Returns:
        LidlTicketDTO: Structured ticket data
    """
    url = LidlConfig.get_receipt_url(receipt_id)
    full_url = f"{url}?country={LidlConfig.get_country_code()}&languageCode={LidlConfig.get_language_code()}"

    response = _request_with_retry(
        session, full_url, timeout=LidlConfig.DEFAULT_TIMEOUT
    )
    if response is None:
        raise requests.exceptions.ConnectionError(
            f"Lidl-Ticket {receipt_id} konnte nach {LidlConfig.MAX_RETRIES} Versuchen nicht abgerufen werden"
        )

    response.raise_for_status()

    data = response.json()
    ticket_data = data["ticket"] if "ticket" in data else data
    return LidlTicketDTO.from_api_response(ticket_data, receipt_id)


def collect_lidl_receipt_ids(
    session: requests.Session, max_pages: Optional[int] = None
) -> Tuple[List[str], int]:
    """Collect LIDL receipt ids from all pages or only a limited number."""
    all_receipt_ids: List[str] = []
    current_page = 1
    processed_pages = 0

    while max_pages is None or current_page <= max_pages:
        tickets_page = get_tickets_page(session, current_page)
        if not tickets_page or not tickets_page.receipt_ids:
            break

        all_receipt_ids.extend(tickets_page.receipt_ids)
        processed_pages = current_page
        current_page += 1

        page_size = len(tickets_page.receipt_ids)
        total_pages = (
            (tickets_page.total_count + page_size - 1) // page_size
            if page_size > 0
            else 1
        )
        if current_page > total_pages:
            break

        if LidlConfig.REQUEST_DELAY > 0:
            time.sleep(LidlConfig.REQUEST_DELAY)

    return all_receipt_ids, processed_pages


def test_lidl_session(session: requests.Session) -> bool:
    """Perform a lightweight session test against the Lidl tickets endpoint."""
    url = (
        f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page=1"
    )
    response = _request_with_retry(session, url, timeout=LidlConfig.DEFAULT_TIMEOUT)
    if response is None:
        return False
    try:
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError:
        return False
