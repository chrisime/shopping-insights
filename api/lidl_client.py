"""Lidl API client for fetching receipt data."""

import json
from typing import Optional, Dict, Any
import requests

from config import LidlConfig


def get_tickets_page(
    session: requests.Session, page: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Fetch tickets for a specific page using the API.

    Args:
        session: requests.Session with authentication
        page: Page number to fetch

    Returns:
        dict: API response data or None if error
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
            # Direct array of tickets
            return {
                "items": data,
                "page": page,
                "size": len(data),
                "totalCount": len(data),
            }
        elif isinstance(data, dict):
            # Structured response with metadata
            return data
        else:
            return None

    except requests.exceptions.HTTPError as e:
        return None
    except requests.exceptions.RequestException as e:
        return None
    except json.JSONDecodeError as e:
        return None


def get_lidl_ticket(
    session: requests.Session, receipt_id: str
) -> Dict[str, Any]:
    """
    Fetch the raw Lidl ticket payload for a specific receipt.

    Args:
        session: requests.Session with authentication
        receipt_id: Receipt ID to fetch

    Returns:
        dict: Raw ticket payload from the Lidl API
    """
    url = LidlConfig.get_receipt_url(receipt_id)
    full_url = f"{url}?country={LidlConfig.get_country_code()}&languageCode={LidlConfig.get_language_code()}"

    response = session.get(full_url, timeout=LidlConfig.DEFAULT_TIMEOUT)
    response.raise_for_status()

    data = response.json()
    return data["ticket"] if "ticket" in data else data


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
    except json.JSONDecodeError:
        return False


test_lidl_session.__test__ = False
