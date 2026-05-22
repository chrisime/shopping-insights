"""Lidl API client for fetching receipt data."""

import simplejson
from typing import Optional
import requests

from config import LidlConfig
from shared.lidl_ticket_dto import LidlTicketDTO, LidlTicketsPageDTO


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
    try:
        response = session.get(
            f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page={page}",
            timeout=LidlConfig.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        # Handle different response structures
        if isinstance(data, list):
            # Direct array of tickets - wrap in standard pagination format
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
            # Structured response with metadata
            return LidlTicketsPageDTO.from_api_response(data, page=page)
        else:
            return None

    except requests.exceptions.HTTPError as e:
        return None
    except requests.exceptions.RequestException as e:
        return None
    except simplejson.JSONDecodeError as e:
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

    response = session.get(full_url, timeout=LidlConfig.DEFAULT_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    ticket_data = data["ticket"] if "ticket" in data else data
    return LidlTicketDTO.from_api_response(ticket_data, receipt_id)


def test_lidl_session(session: requests.Session) -> bool:
    """Perform a lightweight session test against the Lidl tickets endpoint."""
    try:
        response = session.get(
            f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page=1",
            timeout=LidlConfig.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("items") if isinstance(data, dict) else None
        if isinstance(items, list):
            return True

        return True
    except requests.exceptions.HTTPError:
        return False
    except requests.exceptions.RequestException:
        return False
    except simplejson.JSONDecodeError:
        return False


test_lidl_session.__test__ = False
