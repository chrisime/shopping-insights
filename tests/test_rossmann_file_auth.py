import io
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auth.rossmann_file_auth import (
    diagnose_rossmann_cookie_file,
    load_rossmann_cookies_from_file,
    read_rossmann_account,
)


def _rossmann_cookie_json() -> str:
    return json.dumps(
        [
            {"name": "SAP_SESSIONID", "value": "abc", "domain": ".rossmann.de", "path": "/"},
            {"name": "other", "value": "x", "domain": ".rossmann.net", "path": "/"},
            {"accountId": "acct-1", "accountHash": "hsh-1"},
        ]
    )


def _write_cookie_file(directory: Path, content: str) -> Path:
    path = directory / "rossmann_cookies.json"
    path.write_text(content, encoding="utf-8")
    return path


class LoadRossmannCookiesTests(unittest.TestCase):
    def test_loads_cookies(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_cookie_file(Path(tmp), _rossmann_cookie_json())
            session = load_rossmann_cookies_from_file(str(path))
        if session is None:
            self.fail("expected session")
        self.assertEqual(len(session.cookies), 2)

    def test_returns_none_for_missing_file(self):
        self.assertIsNone(load_rossmann_cookies_from_file("nope.json"))

    def test_returns_none_for_missing_cookies(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_cookie_file(Path(tmp), "[]")
            session = load_rossmann_cookies_from_file(str(path))
        self.assertIsNone(session)


class DiagnoseRossmannCookieFileTests(unittest.TestCase):
    def test_returns_false_for_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_cookie_file(Path(tmp), "[]")
            result = diagnose_rossmann_cookie_file(str(path))
        self.assertFalse(result)

    def test_returns_false_for_missing_file(self):
        self.assertFalse(diagnose_rossmann_cookie_file("nope.json"))


class ReadRossmannAccountTests(unittest.TestCase):
    def test_reads_account_from_export(self):
        account = read_rossmann_account(json.dumps({"accountId": "a", "accountHash": "h"}))
        self.assertEqual(account, {"accountId": "a", "accountHash": "h"})

    def test_returns_none_without_account_fields(self):
        self.assertIsNone(read_rossmann_account('[{"name":"x","value":"1"}]'))


class RossmannCookieLoggingTests(unittest.TestCase):
    def test_live_logging_outputs_cookie_count(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("auth.rossmann_file_auth")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = _write_cookie_file(Path(tmp), _rossmann_cookie_json())
                load_rossmann_cookies_from_file(str(path))
        finally:
            logger.removeHandler(handler)
        self.assertIn("Rossmann-Cookies geladen", stream.getvalue())


if __name__ == "__main__":
    unittest.main()