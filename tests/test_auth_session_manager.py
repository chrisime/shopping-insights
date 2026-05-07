import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from auth.lidl_file_auth import load_lidl_cookies_from_file
from auth.session_manager import _load_session_for_retailer, setup_session
from config.lidl_config import LidlConfig


class AuthSessionManagerTests(unittest.TestCase):
    def test_lidl_supports_librewolf_via_generic_session_loader(self):
        session = object()
        extractor_cls = Mock()
        extractor_cls.return_value.extract.return_value = session
        with patch.dict(
            "auth.session_manager.RETAILER_BROWSER_EXTRACTORS",
            {"lidl": extractor_cls},
        ):

            result = _load_session_for_retailer(
                retailer="lidl",
                auth_method="librewolf",
                cookies_file=None,
            )

        self.assertIs(result, session)
        extractor_cls.return_value.extract.assert_called_once_with("librewolf")

    def test_setup_session_uses_generic_rewe_browser_loader(self):
        session = object()
        extractor_cls = Mock()
        extractor_cls.return_value.extract.return_value = session
        with patch.dict(
            "auth.session_manager.RETAILER_BROWSER_EXTRACTORS",
            {"rewe": extractor_cls},
        ):
            result = setup_session(retailer="rewe", auth_method="firefox")

        self.assertIs(result, session)
        extractor_cls.return_value.extract.assert_called_once_with("firefox")

    def test_lidl_file_auth_respects_active_country_domain(self):
        original_country = LidlConfig.COUNTRY
        try:
            LidlConfig.set_country("bg")
            cookies_payload = [
                {
                    "domain": ".lidl.bg",
                    "name": "authToken",
                    "value": "abc",
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                },
                {
                    "domain": ".lidl.de",
                    "name": "ignored",
                    "value": "def",
                    "path": "/",
                    "secure": True,
                    "expirationDate": 1893456000,
                },
            ]
            with tempfile.TemporaryDirectory() as tmp_dir:
                cookie_file = Path(tmp_dir) / "cookies.json"
                cookie_file.write_text(json.dumps(cookies_payload), encoding="utf-8")

                session = load_lidl_cookies_from_file(str(cookie_file))

            self.assertIsNotNone(session)
            self.assertEqual({cookie.name for cookie in session.cookies}, {"authToken"})
        finally:
            LidlConfig.set_country(original_country)


if __name__ == "__main__":
    unittest.main()

