import io
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auth.dm_file_auth import (
    diagnose_dm_cookie_file,
    load_dm_cookies_from_file,
    _classify_dm_cookie_quality,
)


def _dm_cookie_json() -> str:
    import json

    return json.dumps(
        [
            {"name": "_SI_SID_1.2afbd82dd4000131ae283f46", "value": "sid", "domain": ".dm.de", "path": "/"},
            {"name": "_SI_DID_1.2afbd82dd4000131ae283f46", "value": "did", "domain": ".dm.de", "path": "/"},
            {"name": "sessionid", "value": "host-session", "domain": "signin.dm.de", "path": "/"},
        ]
    )


def _write_cookie_file(directory: Path, content: str) -> Path:
    path = directory / "dm_cookies.json"
    path.write_text(content, encoding="utf-8")
    return path


class DmCookieQualityTests(unittest.TestCase):
    def test_classify_rot_without_session_cookie(self):
        self.assertEqual(_classify_dm_cookie_quality({"cf_clearance"}), "ROT")

    def test_classify_gelb_with_session_but_no_recommended(self):
        self.assertEqual(_classify_dm_cookie_quality({"sessionid"}), "GELB")

    def test_classify_gruen_with_session_and_recommended(self):
        names = {"_SI_SID_1.x", "_SI_DID_1.x"}
        self.assertEqual(_classify_dm_cookie_quality(names), "GRUEN")


class LoadDmCookiesFromFileTests(unittest.TestCase):
    def test_loads_json_cookies(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_cookie_file(Path(tmp_dir), _dm_cookie_json())
            session = load_dm_cookies_from_file(str(path))
        if session is None:
            self.fail("expected cookie session")
        self.assertEqual(len(session.cookies), 3)

    def test_returns_none_for_missing_file(self):
        self.assertIsNone(load_dm_cookies_from_file("does-not-exist.json"))

    def test_returns_none_for_empty_cookie_list(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_cookie_file(Path(tmp_dir), "[]")
            session = load_dm_cookies_from_file(str(path))
        self.assertIsNone(session)


class DiagnoseDmCookieFileTests(unittest.TestCase):
    def test_returns_true_when_live_check_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_cookie_file(Path(tmp_dir), _dm_cookie_json())
            with patch("auth.dm_file_auth._attempt_live_token_check", return_value=True):
                result = diagnose_dm_cookie_file(str(path))
        self.assertTrue(result)

    def test_returns_false_when_live_check_reports_invalid_session(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_cookie_file(Path(tmp_dir), _dm_cookie_json())
            with patch("auth.dm_file_auth._attempt_live_token_check", return_value=False):
                result = diagnose_dm_cookie_file(str(path))
        self.assertFalse(result)

    def test_returns_false_without_session_cookie(self):
        import json

        cookies = json.dumps([{"name": "cf_clearance", "value": "x", "domain": ".dm.de", "path": "/"}])
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write_cookie_file(Path(tmp_dir), cookies)
            with patch("auth.dm_file_auth._attempt_live_token_check", return_value=None):
                result = diagnose_dm_cookie_file(str(path))
        self.assertFalse(result)

    def test_returns_false_for_missing_file(self):
        self.assertFalse(diagnose_dm_cookie_file("does-not-exist.json"))


class DiagnoseDmCookieLoggingTests(unittest.TestCase):
    def test_live_token_check_attempted(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("auth.dm_file_auth")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                path = _write_cookie_file(Path(tmp_dir), _dm_cookie_json())
                with patch("auth.dm_file_auth.acquire_dm_access_token", return_value="tok"):
                    diagnose_dm_cookie_file(str(path))
        finally:
            logger.removeHandler(handler)
        self.assertIn("dm-Session gültig", stream.getvalue())


if __name__ == "__main__":
    unittest.main()