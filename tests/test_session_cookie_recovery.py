import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from auth.session_cookie_recovery import (
    _find_default_profile,
    _find_firefox_profiles_dir,
    _read_jsonlz4,
    _read_pref_value,
    check_sessionstore_privacy_level,
    read_session_cookies_for_domain,
)


class SessionCookieRecoveryTests(unittest.TestCase):
    # --- _find_firefox_profiles_dir ---
    @patch("auth.session_cookie_recovery.platform.system", return_value="Darwin")
    @patch("auth.session_cookie_recovery.Path.home", return_value=Path("/Users/test"))
    def test_find_profiles_dir_darwin_firefox(self, mock_home, mock_system):
        result = _find_firefox_profiles_dir("firefox")
        self.assertEqual(
            result,
            Path("/Users/test/Library/Application Support/Firefox/Profiles"),
        )

    @patch("auth.session_cookie_recovery.platform.system", return_value="Darwin")
    @patch("auth.session_cookie_recovery.Path.home", return_value=Path("/Users/test"))
    def test_find_profiles_dir_darwin_librewolf(self, mock_home, mock_system):
        result = _find_firefox_profiles_dir("librewolf")
        self.assertEqual(
            result,
            Path("/Users/test/Library/Application Support/LibreWolf/Profiles"),
        )

    @patch("auth.session_cookie_recovery.platform.system", return_value="Linux")
    @patch("auth.session_cookie_recovery.Path.home", return_value=Path("/home/test"))
    def test_find_profiles_dir_linux_firefox(self, mock_home, mock_system):
        result = _find_firefox_profiles_dir("firefox")
        self.assertEqual(result, Path("/home/test/.mozilla/firefox"))

    @patch("auth.session_cookie_recovery.platform.system", return_value="Linux")
    @patch("auth.session_cookie_recovery.Path.home", return_value=Path("/home/test"))
    def test_find_profiles_dir_linux_librewolf(self, mock_home, mock_system):
        result = _find_firefox_profiles_dir("librewolf")
        self.assertEqual(result, Path("/home/test/.librewolf"))

    @patch("auth.session_cookie_recovery.platform.system", return_value="SunOS")
    def test_find_profiles_dir_unsupported_platform(self, mock_system):
        result = _find_firefox_profiles_dir("firefox")
        self.assertIsNone(result)

    def test_find_profiles_dir_unknown_browser(self):
        with patch(
            "auth.session_cookie_recovery.platform.system", return_value="Darwin"
        ):
            result = _find_firefox_profiles_dir("edge")
            self.assertIsNone(result)

    # --- _find_default_profile ---
    def test_find_default_profile_returns_none_when_dir_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nonexistent"
            result = _find_default_profile(missing)
            self.assertIsNone(result)

    def _make_profile_with_cookies(self, profiles_dir: Path, name: str) -> None:
        profile_dir = profiles_dir / name
        profile_dir.mkdir(parents=True)
        (profile_dir / "cookies.sqlite").touch()

    def test_find_default_profile_prefers_default_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            self._make_profile_with_cookies(profiles_dir, "other")
            self._make_profile_with_cookies(profiles_dir, "xyz456.default")
            self._make_profile_with_cookies(profiles_dir, "abc123.default-release")

            result = _find_default_profile(profiles_dir)
            self.assertIn("default-release", result.name)

    def test_find_default_profile_falls_back_to_any_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            self._make_profile_with_cookies(profiles_dir, "random-profile")

            result = _find_default_profile(profiles_dir)
            self.assertEqual(result.name, "random-profile")

    def test_find_default_profile_returns_none_when_no_cookies_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            (profiles_dir / "empty-profile").mkdir()

            result = _find_default_profile(profiles_dir)
            self.assertIsNone(result)

    def test_find_default_profile_skips_bkp_in_initial_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            profiles_dir = Path(tmp)
            self._make_profile_with_cookies(profiles_dir, "profile.bkp")
            self._make_profile_with_cookies(profiles_dir, "normal-profile")

            result = _find_default_profile(profiles_dir)
            self.assertEqual(result.name, "normal-profile")

    # --- _read_pref_value ---
    def test_read_pref_value_finds_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs = Path(tmp) / "prefs.js"
            prefs.write_text(
                'user_pref("browser.sessionstore.privacy_level", 2);\n'
                'user_pref("other.pref", "hello");\n'
            )
            result = _read_pref_value(prefs, "browser.sessionstore.privacy_level")
            self.assertEqual(result, "2")

    def test_read_pref_value_returns_none_when_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs = Path(tmp) / "prefs.js"
            prefs.write_text('user_pref("other.pref", "hello");\n')
            result = _read_pref_value(prefs, "browser.sessionstore.privacy_level")
            self.assertIsNone(result)

    def test_read_pref_value_returns_none_for_io_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.js"
            result = _read_pref_value(missing, "some.pref")
            self.assertIsNone(result)

    def test_read_pref_value_handles_extra_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs = Path(tmp) / "prefs.js"
            prefs.write_text('user_pref( "privacy.level" , 0 );\n')
            result = _read_pref_value(prefs, "privacy.level")
            self.assertEqual(result, "0")

    def test_read_pref_value_matches_quoted_string_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            prefs = Path(tmp) / "prefs.js"
            prefs.write_text('user_pref("my.pref", "string_val");\n')
            result = _read_pref_value(prefs, "my.pref")
            self.assertEqual(result, "string_val")

    # --- _read_jsonlz4 ---
    def test_read_jsonlz4_returns_none_on_io_error(self):
        result = _read_jsonlz4(Path("/nonexistent/recovery.jsonlz4"))
        self.assertIsNone(result)

    def test_read_jsonlz4_returns_none_on_bad_magic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "recovery.jsonlz4"
            path.write_bytes(b"notMozLz4")
            result = _read_jsonlz4(path)
            self.assertIsNone(result)

    # --- read_session_cookies_for_domain ---
    @patch(
        "auth.session_cookie_recovery._find_firefox_profiles_dir", return_value=None
    )
    def test_read_session_cookies_returns_empty_when_no_profiles_dir(self, mock_find):
        result = read_session_cookies_for_domain("firefox", "rewe.de")
        self.assertEqual(result, [])

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile", return_value=None)
    def test_read_session_cookies_returns_empty_when_no_profile(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        result = read_session_cookies_for_domain("firefox", "rewe.de")
        self.assertEqual(result, [])

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile")
    def test_read_session_cookies_filters_by_domain(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        profile = MagicMock()
        recovery = MagicMock()
        recovery.exists.return_value = True
        profile.__truediv__.return_value = recovery
        mock_default.return_value = profile

        mock_data = {
            "cookies": [
                {"host": "www.rewe.de", "name": "rstp", "value": "abc"},
                {"host": "other.com", "name": "x", "value": "y"},
            ],
            "windows": [],
        }
        with patch(
            "auth.session_cookie_recovery._read_jsonlz4", return_value=mock_data
        ):
            result = read_session_cookies_for_domain("firefox", "rewe.de")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "rstp")

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile")
    def test_read_session_cookies_extracts_from_windows(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        profile = MagicMock()
        recovery = MagicMock()
        recovery.exists.return_value = True
        profile.__truediv__.return_value = recovery
        mock_default.return_value = profile

        mock_data = {
            "cookies": [],
            "windows": [
                {
                    "cookies": [
                        {"host": "lidl.de", "name": "authToken", "value": "tok"}
                    ]
                }
            ],
        }
        with patch(
            "auth.session_cookie_recovery._read_jsonlz4", return_value=mock_data
        ):
            result = read_session_cookies_for_domain("firefox", "lidl.de")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "authToken")

    # --- check_sessionstore_privacy_level ---
    @patch(
        "auth.session_cookie_recovery._find_firefox_profiles_dir", return_value=None
    )
    def test_check_privacy_level_returns_none_when_no_profiles_dir(self, mock_find):
        result = check_sessionstore_privacy_level("firefox")
        self.assertIsNone(result)

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile", return_value=None)
    def test_check_privacy_level_returns_none_when_no_profile(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        result = check_sessionstore_privacy_level("firefox")
        self.assertIsNone(result)

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile")
    def test_check_privacy_level_returns_false_when_level_2(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        profile = MagicMock()
        prefs = MagicMock()
        prefs.exists.return_value = True
        profile.__truediv__.return_value = prefs
        mock_default.return_value = profile

        with patch(
            "auth.session_cookie_recovery._read_pref_value", return_value="2"
        ):
            result = check_sessionstore_privacy_level("firefox")
            self.assertIs(result, False)

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile")
    def test_check_privacy_level_returns_true_when_level_1(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        profile = MagicMock()
        prefs = MagicMock()
        prefs.exists.return_value = True
        profile.__truediv__.return_value = prefs
        mock_default.return_value = profile

        with patch(
            "auth.session_cookie_recovery._read_pref_value", return_value="1"
        ):
            result = check_sessionstore_privacy_level("firefox")
            self.assertIs(result, True)

    @patch("auth.session_cookie_recovery._find_firefox_profiles_dir")
    @patch("auth.session_cookie_recovery._find_default_profile")
    def test_check_privacy_level_returns_none_when_pref_not_set(
        self, mock_default, mock_find
    ):
        mock_find.return_value = Path("/tmp/profiles")
        profile = MagicMock()
        prefs = MagicMock()
        prefs.exists.return_value = True
        profile.__truediv__.return_value = prefs
        mock_default.return_value = profile

        with patch(
            "auth.session_cookie_recovery._read_pref_value", return_value=None
        ):
            result = check_sessionstore_privacy_level("firefox")
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
