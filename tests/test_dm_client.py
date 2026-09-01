import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from client.dm_client import (
    collect_dm_purchases,
    download_ebon_pdf,
    fetch_ebon_detail,
    fetch_purchase_history,
    test_dm_session,
)


def _json_response(payload, status_code=200):
    response = Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.json.return_value = payload
    return response


class FetchPurchaseHistoryTests(unittest.TestCase):
    def test_returns_parsed_json_on_success(self):
        session = Mock()
        session.get.return_value = _json_response({"hasMoreElements": False, "purchaseHistoryItems": []})
        result = fetch_purchase_history(session)
        self.assertEqual(result, {"hasMoreElements": False, "purchaseHistoryItems": []})

    def test_includes_size_and_cursor_params(self):
        session = Mock()
        session.get.return_value = _json_response({"purchaseHistoryItems": []})
        fetch_purchase_history(session, until_date_time_placed="2026-01-07T00:00:00Z", size=20)
        _, kwargs = session.get.call_args
        self.assertEqual(kwargs["params"]["size"], 20)
        self.assertEqual(kwargs["params"]["untilDateTimePlaced"], "2026-01-07T00:00:00Z")

    def test_returns_none_on_non_ok(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=403)
        self.assertIsNone(fetch_purchase_history(session))

    def test_returns_none_on_invalid_json(self):
        session = Mock()
        response = _json_response({})
        response.json.side_effect = ValueError("bad json")
        session.get.return_value = response
        self.assertIsNone(fetch_purchase_history(session))

    def test_returns_none_on_network_error(self):
        session = Mock()
        session.get.side_effect = requests.exceptions.ConnectionError("down")
        self.assertIsNone(fetch_purchase_history(session))


class CollectDmPurchasesTests(unittest.TestCase):
    def test_stops_when_no_more_elements(self):
        session = Mock()
        session.get.side_effect = [
            _json_response({
                "hasMoreElements": False,
                "purchaseHistoryItems": [{"id": "a_2026", "purchaseType": "MARKET"}],
            })
        ]
        purchases = collect_dm_purchases(session)
        self.assertEqual(len(purchases), 1)
        session.get.assert_called_once()

    def test_paginates_until_has_more_is_false(self):
        session = Mock()
        session.get.side_effect = [
            _json_response({
                "hasMoreElements": True,
                "purchaseHistoryItems": [{"id": "a_2026", "dateTimePlaced": "2026-01-07T00:00:00Z"}],
            }),
            _json_response({
                "hasMoreElements": False,
                "purchaseHistoryItems": [{"id": "b_2025", "dateTimePlaced": "2025-01-07T00:00:00Z"}],
            }),
        ]
        with patch("client.dm_client.time.sleep"):
            purchases = collect_dm_purchases(session)
        self.assertEqual([p["id"] for p in purchases], ["a_2026", "b_2025"])

    def test_stops_on_failed_page(self):
        session = Mock()
        session.get.side_effect = [
            _json_response({"hasMoreElements": True, "purchaseHistoryItems": [{"id": "a_2026", "dateTimePlaced": "2026-01-07T00:00:00Z"}]}),
            _json_response({}, status_code=403),
        ]
        with patch("client.dm_client.time.sleep"):
            purchases = collect_dm_purchases(session)
        self.assertEqual([p["id"] for p in purchases], ["a_2026"])

    def test_returns_empty_on_first_page_failure(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=403)
        self.assertEqual(collect_dm_purchases(session), [])


class FetchEbonDetailTests(unittest.TestCase):
    def test_returns_dict_on_success(self):
        session = Mock()
        session.get.return_value = _json_response({"id": "abc_2026", "totalAmount": 5.28})
        result = fetch_ebon_detail(session, "abc_2026")
        if result is None:
            self.fail("expected ebon detail dict")
        self.assertEqual(result["totalAmount"], 5.28)

    def test_returns_none_on_non_dict(self):
        session = Mock()
        session.get.return_value = _json_response(["not", "a", "dict"])
        self.assertIsNone(fetch_ebon_detail(session, "abc_2026"))

    def test_returns_none_on_non_ok(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=404)
        self.assertIsNone(fetch_ebon_detail(session, "abc_2026"))


class DownloadEbonPdfTests(unittest.TestCase):
    def test_downloads_pdf(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.iter_content.return_value = [b"%PDF-1.4", b"data"]
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "abc_2026.pdf"
            result = download_ebon_pdf(session, "abc_2026", output)
            self.assertEqual(result, output)
            self.assertEqual(output.read_bytes(), b"%PDF-1.4data")

    def test_returns_none_on_non_ok(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=403)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "abc_2026.pdf"
            self.assertIsNone(download_ebon_pdf(session, "abc_2026", output))


class DmClientRetryTests(unittest.TestCase):
    def test_retries_on_429_then_succeeds(self):
        session = Mock()
        session.get.side_effect = [
            _json_response({}, status_code=429),
            _json_response({"purchaseHistoryItems": []}),
        ]
        with patch("client.dm_client.time.sleep"):
            result = fetch_purchase_history(session)
        self.assertIsNotNone(result)

    def test_retries_on_500_then_succeeds(self):
        session = Mock()
        session.get.side_effect = [
            _json_response({}, status_code=500),
            _json_response({"purchaseHistoryItems": []}),
        ]
        with patch("client.dm_client.time.sleep"):
            result = fetch_purchase_history(session)
        self.assertIsNotNone(result)

    def test_returns_response_after_exhausted_retries(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=429)
        with patch("client.dm_client.time.sleep"):
            result = fetch_purchase_history(session)
        self.assertIsNone(result)

    def test_401_triggers_token_refresh_and_retries(self):
        session = Mock()
        session.headers = {}
        session.get.side_effect = [
            _json_response({}, status_code=401),
            _json_response({"purchaseHistoryItems": []}),
        ]
        refresher = Mock(return_value="new-token")
        result = fetch_purchase_history(session, token_refresher=refresher)
        self.assertIsNotNone(result)
        refresher.assert_called_once()
        self.assertEqual(session.headers["Authorization"], "Bearer new-token")

    def test_401_without_refresh_returns_none(self):
        session = Mock()
        session.headers = {}
        session.get.return_value = _json_response({}, status_code=401)
        self.assertIsNone(fetch_purchase_history(session))


class TestDmSessionTests(unittest.TestCase):
    def test_test_dm_session_true_on_success(self):
        session = Mock()
        session.get.return_value = _json_response({"purchaseHistoryItems": []})
        self.assertTrue(test_dm_session(session))

    def test_test_dm_session_false_on_failure(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=403)
        self.assertFalse(test_dm_session(session))


if __name__ == "__main__":
    unittest.main()