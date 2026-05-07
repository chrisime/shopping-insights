import io
import unittest

import requests
from unittest.mock import patch

from auth.lidl_browser_auth import LidlBrowserCookieExtractor
from auth.shared_file_auth import build_cookie_session, validate_cookie_names


class AuthCookieValidationTests(unittest.TestCase):
    def test_validate_cookie_names_reports_missing_required_and_present_recommended(self):
        validation = validate_cookie_names(
            {"authToken", "XSRF-TOKEN"},
            required_cookies={"authToken", "ldi-customertoken"},
            recommended_cookies={"XSRF-TOKEN", "ldi-user-context"},
        )

        self.assertEqual(validation.missing_required, ("ldi-customertoken",))
        self.assertEqual(validation.present_recommended, ("XSRF-TOKEN",))
        self.assertEqual(validation.missing_recommended, ("ldi-user-context",))
        self.assertTrue(validation.has_any_recommended)

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

        cookies = list(session.cookies)
        self.assertEqual(cookie_count, 1)
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0].value, "new")
        self.assertTrue(cookies[0].secure)
        self.assertEqual(cookies[0].path, "/")

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

