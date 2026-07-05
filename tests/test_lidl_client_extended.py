import unittest
from unittest.mock import Mock, patch

import simplejson

from client.lidl_client import _request_with_retry, collect_lidl_receipt_ids, get_tickets_page
from shared.lidl_ticket_dto import LidlTicketsPageDTO


class LidlClientExtendedTests(unittest.TestCase):
    # --- get_tickets_page ---
    def _mock_response(self, ok: bool, json_data=None):
        resp = Mock()
        resp.ok = ok
        resp.json.return_value = json_data or {}
        resp.status_code = 200 if ok else 500
        return resp

    def test_get_tickets_page_returns_page_dto_for_list_response(self):
        session = Mock()
        response = self._mock_response(
            True,
            [
                {"id": "1", "isHtml": True},
                {"id": "2", "isHtml": False},
            ],
        )
        session.get.return_value = response

        result = get_tickets_page(session, page=1)
        self.assertIsInstance(result, LidlTicketsPageDTO)
        self.assertEqual(result.receipt_ids, ["1"])

    def test_get_tickets_page_returns_page_dto_for_dict_response(self):
        session = Mock()
        response = self._mock_response(
            True,
            {
                "items": [{"id": "10", "isHtml": True}],
                "totalCount": 1,
            },
        )
        session.get.return_value = response

        result = get_tickets_page(session, page=2)
        self.assertIsInstance(result, LidlTicketsPageDTO)
        self.assertEqual(result.receipt_ids, ["10"])

    def test_get_tickets_page_returns_none_when_request_fails(self):
        session = Mock()
        with patch("client.lidl_client._request_with_retry", return_value=None):
            result = get_tickets_page(session, page=1)
        self.assertIsNone(result)

    def test_get_tickets_page_returns_none_when_json_decode_fails(self):
        session = Mock()
        resp = Mock()
        resp.ok = True
        resp.json.side_effect = simplejson.JSONDecodeError("bad json", "", 0)
        session.get.return_value = resp

        result = get_tickets_page(session, page=1)
        self.assertIsNone(result)

    def test_get_tickets_page_returns_none_for_unexpected_type(self):
        session = Mock()
        resp = Mock()
        resp.ok = True
        resp.json.return_value = 42
        session.get.return_value = resp

        result = get_tickets_page(session, page=1)
        self.assertIsNone(result)

    # --- collect_lidl_receipt_ids ---
    def test_collect_lidl_receipt_ids_collects_from_multiple_pages(self):
        session = Mock()

        page1 = LidlTicketsPageDTO(receipt_ids=["a", "b"], page=1, total_count=4)
        page2 = LidlTicketsPageDTO(receipt_ids=["c", "d"], page=2, total_count=4)

        with (
            patch("client.lidl_client.get_tickets_page") as mock_get,
            patch("client.lidl_client.time.sleep"),
        ):
            mock_get.side_effect = [page1, page2]
            ids, pages = collect_lidl_receipt_ids(session)

        self.assertEqual(ids, ["a", "b", "c", "d"])
        self.assertEqual(pages, 2)

    def test_collect_lidl_receipt_ids_stops_when_no_more_tickets(self):
        session = Mock()
        page1 = LidlTicketsPageDTO(receipt_ids=["a"], page=1, total_count=0)

        with (
            patch("client.lidl_client.get_tickets_page") as mock_get,
            patch("client.lidl_client.time.sleep"),
        ):
            mock_get.side_effect = [page1, None]
            ids, pages = collect_lidl_receipt_ids(session)

        self.assertEqual(ids, ["a"])
        self.assertEqual(pages, 1)

    def test_collect_lidl_receipt_ids_stops_when_page_returns_none(self):
        session = Mock()
        with patch("client.lidl_client.get_tickets_page", return_value=None):
            ids, pages = collect_lidl_receipt_ids(session)

        self.assertEqual(ids, [])
        self.assertEqual(pages, 0)

    def test_collect_lidl_receipt_ids_respects_max_pages(self):
        session = Mock()
        page1 = LidlTicketsPageDTO(receipt_ids=["a"], page=1, total_count=10)
        page2 = LidlTicketsPageDTO(receipt_ids=["b"], page=2, total_count=10)

        with (
            patch("client.lidl_client.get_tickets_page") as mock_get,
            patch("client.lidl_client.time.sleep"),
        ):
            mock_get.side_effect = [page1, page2]
            ids, pages = collect_lidl_receipt_ids(session, max_pages=1)

        self.assertEqual(ids, ["a"])
        self.assertEqual(pages, 1)


if __name__ == "__main__":
    unittest.main()
