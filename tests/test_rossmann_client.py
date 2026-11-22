import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from client.rossmann_client import (
    collect_rossmann_receipts,
    download_receipt_pdf,
    fetch_receipt_detail,
    fetch_receipts,
    test_rossmann_session,
)


def _json_response(payload, status_code=200, headers=None):
    response = Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.json.return_value = payload
    response.headers = headers or {}
    return response


class FetchReceiptsTests(unittest.TestCase):
    def test_returns_page_and_token(self):
        session = Mock()
        session.get.return_value = _json_response(
            [{"id": "r1"}], headers={"ContinuationToken": "tok-2"}
        )
        page, token = fetch_receipts(session)
        self.assertEqual(page, [{"id": "r1"}])
        self.assertEqual(token, "tok-2")
        _, kwargs = session.get.call_args
        self.assertEqual(kwargs["params"]["take"], 20)
        self.assertNotIn("continuationToken", kwargs["params"])

    def test_returns_none_on_non_ok(self):
        session = Mock()
        session.get.return_value = _json_response([], status_code=403)
        page, token = fetch_receipts(session)
        self.assertIsNone(page)
        self.assertIsNone(token)


class CollectRossmannReceiptsTests(unittest.TestCase):
    def test_paginates_until_token_end(self):
        session = Mock()
        session.get.side_effect = [
            _json_response([{"id": "1"}], headers={"ContinuationToken": "tok-2"}),
            _json_response([{"id": "2"}], headers={}),
        ]
        with patch("client.rossmann_client.time.sleep"):
            receipts = collect_rossmann_receipts(session)
        self.assertEqual([r["id"] for r in receipts], ["1", "2"])

    def test_stops_on_failed_page(self):
        session = Mock()
        session.get.side_effect = [
            _json_response([{"id": "1"}], headers={"ContinuationToken": "tok-2"}),
            _json_response([], status_code=403),
        ]
        with patch("client.rossmann_client.time.sleep"):
            receipts = collect_rossmann_receipts(session)
        self.assertIsNone(receipts)


class FetchReceiptDetailTests(unittest.TestCase):
    def test_returns_dict(self):
        session = Mock()
        session.get.return_value = _json_response({"id": "r1"})
        detail = fetch_receipt_detail(session, "r1")
        if detail is None:
            self.fail("expected detail")
        self.assertEqual(detail["id"], "r1")

    def test_returns_none_on_non_ok(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=404)
        self.assertIsNone(fetch_receipt_detail(session, "r1"))


class DownloadReceiptPdfTests(unittest.TestCase):
    def test_downloads_pdf(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.ok = True
        response.iter_content.return_value = [b"%PDF-1.4", b"data"]
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "r1.pdf"
            result = download_receipt_pdf(session, "r1", output)
            self.assertEqual(result, output)
            self.assertEqual(output.read_bytes(), b"%PDF-1.4data")

    def test_returns_none_on_non_ok(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=403)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "r1.pdf"
            self.assertIsNone(download_receipt_pdf(session, "r1", output))


class RossmannClientRetryTests(unittest.TestCase):
    def test_401_triggers_refresh_and_retries(self):
        session = Mock()
        session.headers = {}
        session.get.side_effect = [
            _json_response([], status_code=401),
            _json_response([{"id": "1"}]),
        ]
        refresher = Mock(return_value="new-token")
        page, token = fetch_receipts(session, token_refresher=refresher)
        self.assertEqual(page, [{"id": "1"}])
        refresher.assert_called_once()
        self.assertEqual(session.headers["Authorization"], "Bearer new-token")

    def test_retries_on_429_then_succeeds(self):
        session = Mock()
        session.get.side_effect = [
            _json_response([], status_code=429),
            _json_response([{"id": "1"}]),
        ]
        with patch("client.rossmann_client.time.sleep"):
            page, _ = fetch_receipts(session)
        self.assertEqual(page, [{"id": "1"}])


class TestRossmannSessionTests(unittest.TestCase):
    def test_true_on_success(self):
        session = Mock()
        session.get.return_value = _json_response([], headers={})
        self.assertTrue(test_rossmann_session(session))

    def test_false_on_failure(self):
        session = Mock()
        session.get.return_value = _json_response([], status_code=403)
        self.assertFalse(test_rossmann_session(session))


if __name__ == "__main__":
    unittest.main()
