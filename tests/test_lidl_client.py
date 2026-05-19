import unittest
from unittest.mock import Mock

from api.lidl_client import get_lidl_ticket, test_lidl_session


class LidlClientTests(unittest.TestCase):
    def test_get_lidl_ticket_returns_nested_ticket_payload(self):
        session = Mock()
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "ticket": {
                "date": "19.08.2024",
                "store": {"name": "Fürth-Südstadt"},
                "htmlPrintedReceipt": "",
            }
        }
        session.get.return_value = response

        result = get_lidl_ticket(
            session,
            "230058821020240819725516",
        )

        self.assertEqual(result["date"], "19.08.2024")
        self.assertEqual(result["store"], {"name": "Fürth-Südstadt"})

    def test_get_lidl_ticket_accepts_direct_ticket_payload(self):
        session = Mock()
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "date": "19.08.2024",
            "store": {"name": "Fürth-Südstadt"},
            "htmlPrintedReceipt": "<html><body></body></html>",
        }
        session.get.return_value = response

        result = get_lidl_ticket(
            session,
            "230058821020240819725516",
        )

        self.assertEqual(result["date"], "19.08.2024")
        self.assertEqual(result["store"], {"name": "Fürth-Südstadt"})

    def test_test_lidl_session_returns_true_when_tickets_endpoint_is_accessible(self):
        session = Mock()
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"items": [], "totalCount": 0}
        session.get.return_value = response

        result = test_lidl_session(session)

        self.assertTrue(result)

    def test_test_lidl_session_returns_false_on_unauthorized(self):
        session = Mock()
        response = Mock()
        response.status_code = 401

        import requests

        session.get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)

        result = test_lidl_session(session)

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

