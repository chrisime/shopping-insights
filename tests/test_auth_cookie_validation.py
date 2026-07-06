import unittest
import base64
import simplejson
from http.cookiejar import Cookie
from typing import cast

import requests

from auth.lidl_browser_auth import LidlBrowserCookieExtractor
from auth.rewe_browser_auth import ReweBrowserCookieExtractor
from auth.shared_file_auth import analyze_cookie_names, build_cookie_session


class AuthCookieValidationTests(unittest.TestCase):
    @staticmethod
    def _build_jwt_like_token(payload: dict) -> str:
        header_raw = simplejson.dumps({"alg": "none", "typ": "JWT"}, separators=(",", ":")).encode("utf-8")
        payload_raw = simplejson.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = base64.urlsafe_b64encode(header_raw).decode("ascii").rstrip("=")
        body = base64.urlsafe_b64encode(payload_raw).decode("ascii").rstrip("=")
        return f"{header}.{body}.sig"

    def test_analyze_cookie_names_reports_missing_required_and_present_recommended(self):
        analysis = analyze_cookie_names(
            {"authToken", "XSRF-TOKEN"},
            required_cookies={"authToken", "ldi-customertoken"},
            recommended_cookies={"XSRF-TOKEN", "ldi-user-context"},
        )

        self.assertEqual(analysis.missing_required, ("ldi-customertoken",))
        self.assertEqual(analysis.present_recommended, ("XSRF-TOKEN",))
        self.assertEqual(analysis.missing_recommended, ("ldi-user-context",))
        self.assertTrue(analysis.present_recommended)

    def test_build_cookie_session_deduplicates_and_normalizes_cookie_shape(self):
        session, cookie_count = build_cookie_session(
            [
                {
                    "domain": ".rewe.de",
                    "name": "rstp",
                    "value": "old",
                    "path": "/",
                    "secure": 1,
                },
                {
                    "domain": ".rewe.de",
                    "name": "rstp",
                    "value": "new",
                    "path": "/",
                    "secure": True,
                },
            ],
        )

        self.assertEqual(cookie_count, 1)
        cookie = cast(Cookie, next(iter(session.cookies)))
        self.assertEqual(cookie.value, "new")
        self.assertTrue(cookie.secure)
        self.assertEqual(cookie.path, "/")

    def test_lidl_browser_validation_reports_missing_required_auth_cookie(self):
        extractor = LidlBrowserCookieExtractor()
        session = requests.Session()
        session.cookies.set("tracking-info", "abc", domain="www.lidl.de", path="/")

        with self.assertLogs("auth", level="INFO") as logs:
            is_valid = extractor._validate_cookies(session, "Firefox")

        output = "\n".join(logs.output)
        self.assertFalse(is_valid)
        self.assertIn("authToken", output)
        self.assertIn("Lidl-Konto-/Kontext-Cookies", output)

    def test_lidl_browser_validation_rejects_expired_auth_token(self):
        extractor = LidlBrowserCookieExtractor()
        session = requests.Session()
        session.cookies.set(
            "authToken",
            self._build_jwt_like_token({"exp": 1}),
            domain="www.lidl.de",
            path="/",
        )

        with self.assertLogs("auth", level="INFO") as logs:
            is_valid = extractor._validate_cookies(session, "Firefox")

        output = "\n".join(logs.output)
        self.assertFalse(is_valid)
        self.assertIn("abgelaufen", output)

    def test_lidl_browser_validation_accepts_valid_auth_token(self):
        extractor = LidlBrowserCookieExtractor()
        session = requests.Session()
        session.cookies.set(
            "authToken",
            self._build_jwt_like_token({"exp": 9999999999}),
            domain="www.lidl.de",
            path="/",
        )

        is_valid = extractor._validate_cookies(session, "Firefox")
        self.assertTrue(is_valid)

    def test_rewe_browser_validation_rejects_expired_rstp(self):
        extractor = ReweBrowserCookieExtractor()
        session = requests.Session()
        session.cookies.set(
            "rstp",
            self._build_jwt_like_token({"exp": 1}),
            domain="www.rewe.de",
            path="/",
        )

        with self.assertLogs("auth", level="INFO") as logs:
            is_valid = extractor._validate_cookies(session, "Firefox")

        output = "\n".join(logs.output)
        self.assertFalse(is_valid)
        self.assertIn("abgelaufen", output)

    def test_rewe_browser_validation_accepts_valid_rstp(self):
        extractor = ReweBrowserCookieExtractor()
        session = requests.Session()
        session.cookies.set(
            "rstp",
            self._build_jwt_like_token({"exp": 9999999999}),
            domain="www.rewe.de",
            path="/",
        )

        is_valid = extractor._validate_cookies(session, "Firefox")
        self.assertTrue(is_valid)

    def test_rewe_browser_missing_required_logs_precise_session_diagnostics(self):
        extractor = ReweBrowserCookieExtractor()
        session = requests.Session()

        with self.assertLogs("auth", level="INFO") as logs:
            with self.assertRaises(Exception) as ctx:
                extractor._validate_cookies(session, "Firefox")

        output = "\n".join(logs.output)
        self.assertIn("sessionstore-backups/recovery.jsonlz4", output)
        self.assertEqual(str(ctx.exception), "rstp fehlt im Browserprofil")

    def test_rewe_browser_load_error_mentions_locked_profile(self):
        extractor = ReweBrowserCookieExtractor()

        with self.assertLogs("auth", level="INFO") as logs:
            with self.assertRaises(Exception) as ctx:
                extractor._on_load_error("Firefox", Exception("database is locked"))

        output = "\n".join(logs.output)
        self.assertIn("vollstaendig schliessen", output)
        self.assertEqual(str(ctx.exception), "Browserprofil gesperrt")


if __name__ == "__main__":
    unittest.main()
