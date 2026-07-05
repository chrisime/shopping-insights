import simplejson
import tempfile
import unittest
import base64
from pathlib import Path
from unittest.mock import Mock

from auth.lidl_file_auth import load_lidl_cookies_from_file
from auth.rewe_customer_id import (
    cache_customer_id,
    extract_rewe_customer_id_from_text,
    _load_cached_customer_id,
    resolve_rewe_customer_id,
)
from auth.rewe_file_auth import load_rewe_cookies_from_file


class AuthFileAuthTests(unittest.TestCase):
    @staticmethod
    def _build_jwt_like_token(payload: dict) -> str:
        header_raw = simplejson.dumps({"alg": "none", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
        payload_raw = simplejson.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = base64.urlsafe_b64encode(header_raw).decode("ascii").rstrip("=")
        body = base64.urlsafe_b64encode(payload_raw).decode("ascii").rstrip("=")
        return f"{header}.{body}.sig"

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
            cookie_file.write_text(simplejson.dumps(cookies_payload), encoding="utf-8")

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
            cookie_file.write_text(simplejson.dumps(cookies_payload), encoding="utf-8")

            session = load_lidl_cookies_from_file(str(cookie_file))

        self.assertIsNone(session)

    def test_load_lidl_cookies_from_file_rejects_expired_auth_token(self):
        expired_token = self._build_jwt_like_token({"exp": 1})
        cookies_payload = {
            "cookies": [
                {
                    "domain": ".lidl.de",
                    "name": "authToken",
                    "value": expired_token,
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "lidl_cookies.json"
            cookie_file.write_text(simplejson.dumps(cookies_payload), encoding="utf-8")

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
            cookie_file.write_text(simplejson.dumps(cookies_payload), encoding="utf-8")

            session = load_rewe_cookies_from_file(str(cookie_file))

        self.assertIsNotNone(session)
        self.assertEqual({cookie.name for cookie in session.cookies}, {"rstp"})

    def test_load_rewe_cookies_from_file_rejects_expired_rstp(self):
        expired_token = self._build_jwt_like_token({"exp": 1})
        cookies_payload = {
            "cookies": [
                {
                    "domain": ".rewe.de",
                    "name": "rstp",
                    "value": expired_token,
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "rewe_cookies.json"
            cookie_file.write_text(simplejson.dumps(cookies_payload), encoding="utf-8")

            session = load_rewe_cookies_from_file(str(cookie_file))

        self.assertIsNone(session)

    def test_extract_rewe_customer_id_from_text_normalizes_uuid(self):
        customer_id = extract_rewe_customer_id_from_text(
            '... customerUUID="12345678-1234-1234-1234-ABCDEFABCDEF" ...'
        )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")

    def test_resolve_rewe_customer_id_prefers_explicit_input(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_customer_id("87654321-4321-4321-4321-fedcbafedcba", Path(tmp_dir))

            customer_id = resolve_rewe_customer_id(
                customer_id="12345678-1234-1234-1234-ABCDEFABCDEF",
                session=None,
                cookies_file=None,
                output_dir=Path(tmp_dir),
            )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")

    def test_resolve_rewe_customer_id_reads_customer_id_from_session_before_file_and_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cookie_file = Path(tmp_dir) / "rewe_input.txt"
            cookie_file.write_text(
                "customerId=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                encoding="utf-8",
            )
            cache_customer_id("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", Path(tmp_dir))

            response = Mock()
            response.status_code = 200
            response.text = '{"customerUUID":"12345678-1234-1234-1234-ABCDEFABCDEF"}'
            response.close = Mock()

            session = Mock()
            session.get.return_value = response

            customer_id = resolve_rewe_customer_id(
                customer_id=None,
                session=session,
                cookies_file=str(cookie_file),
                output_dir=Path(tmp_dir),
            )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")
        response.close.assert_called_once()

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
                output_dir=Path(tmp_dir),
            )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")

    def test_load_cached_customer_id_normalizes_uuid_from_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_customer_id("12345678-1234-1234-1234-ABCDEFABCDEF", Path(tmp_dir))

            customer_id = _load_cached_customer_id(Path(tmp_dir))

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")

    def test_resolve_rewe_customer_id_falls_back_to_cache(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_customer_id("12345678-1234-1234-1234-ABCDEFABCDEF", Path(tmp_dir))

            customer_id = resolve_rewe_customer_id(
                customer_id=None,
                session=None,
                cookies_file=None,
                output_dir=Path(tmp_dir),
            )

        self.assertEqual(customer_id, "12345678-1234-1234-1234-abcdefabcdef")


if __name__ == "__main__":
    unittest.main()
