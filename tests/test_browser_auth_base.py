import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from auth.browser_auth_base import ALL_BROWSER_LOADERS, BrowserCookieExtractor


class _TestExtractor(BrowserCookieExtractor):
    retailer_name = "Test"
    cookie_domain = "test.com"
    supported_browsers = {"firefox": "Firefox", "chrome": "Chrome"}
    required_cookies = {"session_id"}
    recommended_cookies = {"remember_me"}


class BrowserAuthBaseTests(unittest.TestCase):
    # --- ALL_BROWSER_LOADERS ---
    def test_all_browser_loaders_contains_expected_keys(self):
        self.assertIn("firefox", ALL_BROWSER_LOADERS)
        self.assertIn("chrome", ALL_BROWSER_LOADERS)
        self.assertIn("chromium", ALL_BROWSER_LOADERS)
        self.assertIn("librewolf", ALL_BROWSER_LOADERS)

    # --- BrowserCookieExtractor.extract ---
    def _make_mock_cookie(
        self,
        domain: str = ".test.com",
        name: str = "session_id",
        value: str = "abc123",
        secure: bool = True,
        path: str = "/",
    ) -> MagicMock:
        c = MagicMock()
        c.domain = domain
        c.name = name
        c.value = value
        c.secure = secure
        c.path = path
        c.expires = None
        return c

    def test_extract_returns_none_for_unsupported_browser(self):
        extractor = _TestExtractor()
        result = extractor.extract(browser="edge")
        self.assertIsNone(result)

    def test_extract_returns_session_on_success(self):
        mock_loader = MagicMock(return_value=[self._make_mock_cookie()])

        with (
            patch.dict("auth.browser_auth_base.ALL_BROWSER_LOADERS", {"firefox": mock_loader}),
            patch("auth.browser_auth_base.read_session_cookies_for_domain", return_value=[]),
        ):
            extractor = _TestExtractor()
            result = extractor.extract(browser="firefox")

        self.assertIsNotNone(result)
        cookies = list(result.cookies)
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0].name, "session_id")
        self.assertEqual(cookies[0].value, "abc123")

    def test_extract_returns_none_when_loader_fails(self):
        mock_loader = MagicMock(side_effect=Exception("browser not found"))

        with patch.dict("auth.browser_auth_base.ALL_BROWSER_LOADERS", {"firefox": mock_loader}):
            extractor = _TestExtractor()
            result = extractor.extract(browser="firefox")
        self.assertIsNone(result)

    def test_extract_returns_none_when_no_cookies_found(self):
        mock_loader = MagicMock(return_value=[])

        with (
            patch.dict("auth.browser_auth_base.ALL_BROWSER_LOADERS", {"firefox": mock_loader}),
            patch("auth.browser_auth_base.read_session_cookies_for_domain", return_value=[]),
        ):
            extractor = _TestExtractor()
            result = extractor.extract(browser="firefox")
        self.assertIsNone(result)

    def test_extract_returns_none_when_required_cookies_missing(self):
        mock_loader = MagicMock(return_value=[self._make_mock_cookie(name="some_other")])

        with (
            patch.dict("auth.browser_auth_base.ALL_BROWSER_LOADERS", {"firefox": mock_loader}),
            patch("auth.browser_auth_base.read_session_cookies_for_domain", return_value=[]),
        ):
            extractor = _TestExtractor()
            result = extractor.extract(browser="firefox")
        self.assertIsNone(result)

    def test_extract_filter_by_domain_suffix(self):
        mock_loader = MagicMock(
            return_value=[
                self._make_mock_cookie(domain=".test.com", name="session_id", value="ok"),
                self._make_mock_cookie(domain=".evil.com", name="session_id", value="bad"),
            ]
        )

        class _FilterExtractor(_TestExtractor):
            filter_by_domain_suffix = True

        with (
            patch.dict("auth.browser_auth_base.ALL_BROWSER_LOADERS", {"firefox": mock_loader}),
            patch("auth.browser_auth_base.read_session_cookies_for_domain", return_value=[]),
        ):
            extractor = _FilterExtractor()
            result = extractor.extract(browser="firefox")

        self.assertIsNotNone(result)
        cookies = list(result.cookies)
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0].value, "ok")


if __name__ == "__main__":
    unittest.main()
