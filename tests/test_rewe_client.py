import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from client.rewe_client import RETRYABLE_STATUS_CODES, download_receipts_zip, test_rewe_session


class ReweClientTests(unittest.TestCase):
    # --- RETRYABLE_STATUS_CODES ---
    def test_retryable_status_codes_contains_429_and_5xx(self):
        self.assertIn(429, RETRYABLE_STATUS_CODES)
        for code in (500, 502, 503, 504):
            self.assertIn(code, RETRYABLE_STATUS_CODES)

    # --- test_rewe_session ---
    def test_test_rewe_session_returns_true_for_zip_content_type(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.headers = {"content-type": "application/zip"}
        session.get.return_value = response

        self.assertTrue(test_rewe_session(session, "customer-123"))

    def test_test_rewe_session_returns_false_for_non_zip(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.headers = {"content-type": "text/html"}
        session.get.return_value = response

        self.assertFalse(test_rewe_session(session, "customer-123"))

    def test_test_rewe_session_returns_false_for_non_200(self):
        session = Mock()
        response = Mock()
        response.status_code = 403
        session.get.return_value = response

        self.assertFalse(test_rewe_session(session, "customer-123"))

    def test_test_rewe_session_returns_false_on_request_exception(self):
        session = Mock()
        session.get.side_effect = requests.exceptions.ConnectionError("timeout")
        self.assertFalse(test_rewe_session(session, None))

    def test_test_rewe_session_closes_response(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.headers = {"content-type": "application/zip"}
        session.get.return_value = response

        test_rewe_session(session, "customer-123")
        response.close.assert_called_once()

    # --- download_receipts_zip ---
    def test_download_receipts_zip_downloads_successfully(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.iter_content.return_value = [b"chunk1", b"chunk2"]
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "receipts.zip"
            result = download_receipts_zip(session, "customer-123", output)

            self.assertEqual(result, output)
            self.assertTrue(output.exists())
            self.assertEqual(output.read_bytes(), b"chunk1chunk2")

    def test_download_receipts_zip_returns_none_on_non_200(self):
        session = Mock()
        response = Mock()
        response.status_code = 403
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "receipts.zip"
            result = download_receipts_zip(session, "customer-123", output)
            self.assertIsNone(result)

    def test_download_receipts_zip_retries_on_retryable_status(self):
        session = Mock()
        fail_response = Mock()
        fail_response.status_code = 429
        ok_response = Mock()
        ok_response.status_code = 200
        ok_response.iter_content.return_value = [b"data"]
        session.get.side_effect = [fail_response, ok_response]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "receipts.zip"
            with patch("client.rewe_client.time.sleep"):
                result = download_receipts_zip(session, "customer-123", output)

            self.assertEqual(result, output)

    def test_download_receipts_zip_returns_none_on_exhausted_retries(self):
        session = Mock()
        session.get.side_effect = requests.exceptions.ConnectionError("timeout")

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "receipts.zip"
            with patch("client.rewe_client.time.sleep"):
                result = download_receipts_zip(session, "customer-123", output)
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
