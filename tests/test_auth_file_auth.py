import json
import tempfile
import unittest
from pathlib import Path

from auth.lidl_file_auth import load_lidl_cookies_from_file
from auth.rewe_customer_id import extract_rewe_customer_id_from_text, resolve_rewe_customer_id
from auth.rewe_file_auth import load_rewe_cookies_from_file


class AuthFileAuthTests(unittest.TestCase):
    def test_load_lidl_cookies_from_file_accepts_top_level_cookies_key(self):
        cookies_payload = {
            "cookies": [
                {
                    "domain": ".lidl.de",
                    "name": "authToken",
                    "value": "abc",
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "lidl_cookies.json"
            cookie_file.write_text(json.dumps(cookies_payload), encoding="utf-8")

            session = load_lidl_cookies_from_file(str(cookie_file))

        self.assertIsNotNone(session)
        self.assertEqual({cookie.name for cookie in session.cookies}, {"authToken"})

    def test_load_lidl_cookies_from_file_rejects_missing_required_auth_cookie(self):
        cookies_payload = {
            "cookies": [
                {
                    "domain": ".lidl.de",
                    "name": "tracking-info",
                    "value": "abc",
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "lidl_cookies.json"
            cookie_file.write_text(json.dumps(cookies_payload), encoding="utf-8")

            session = load_lidl_cookies_from_file(str(cookie_file))

        self.assertIsNone(session)

    def test_load_rewe_cookies_from_file_accepts_top_level_cookies_key(self):
        cookies_payload = {
            "cookies": [
                {
                    "domain": ".rewe.de",
                    "name": "rstp",
                    "value": "abc",
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                },
                {
                    "domain": ".example.org",
                    "name": "ignored",
                    "value": "def",
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                },
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "rewe_cookies.json"
            cookie_file.write_text(json.dumps(cookies_payload), encoding="utf-8")

            session = load_rewe_cookies_from_file(str(cookie_file))

        self.assertIsNotNone(session)
        self.assertEqual({cookie.name for cookie in session.cookies}, {"rstp"})

    def test_extract_rewe_customer_id_from_text_normalizes_uuid(self):
        customer_id = extract_rewe_customer_id_from_text(
            '... customerUUID="12345678-1234-1234-1234-ABCDEFABCDEF" ...'
        )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")

    def test_resolve_rewe_customer_id_reads_customer_id_from_input_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "rewe_input.txt"
            cookie_file.write_text(
                "customerId=12345678-1234-1234-1234-ABCDEFABCDEF",
                encoding="utf-8",
            )

            customer_id = resolve_rewe_customer_id(
                customer_id=None,
                session=None,
                cookies_file=str(cookie_file),
                output_dir=tmp_dir,
            )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")


if __name__ == "__main__":
    unittest.main()

