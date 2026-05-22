import io
import unittest
from http.cookiejar import Cookie
from typing import cast

import requests
from unittest.mock import patch

from auth.lidl_browser_auth import LidlBrowserCookieExtractor
from auth.shared_file_auth import analyze_cookie_names, build_cookie_session


class AuthCookieValidationTests(unittest.TestCase):
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

        stdout = io.StringIO()
        with patch("sys.stdout", new=stdout):
            is_valid = extractor._validate_cookies(session, "Firefox")

        output = stdout.getvalue()
        self.assertFalse(is_valid)
        self.assertIn("authToken", output)
        self.assertIn("Lidl-Konto-/Kontext-Cookies", output)


if __name__ == "__main__":
    unittest.main()

