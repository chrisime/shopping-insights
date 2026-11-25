import unittest
from unittest.mock import Mock, patch
from uuid import UUID

import requests

from auth.rossmann_auth import (
    RossmannAccount,
    RossmannAuthError,
    build_anybill_api_session,
    login_rossmann_account,
    make_anybill_token_refresher,
    mint_anybill_token,
    prompt_rossmann_login,
)
from config import RossmannConfig


def _json_response(payload, status_code=200):
    response = Mock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.json.return_value = payload
    return response


class LoginRossmannAccountTests(unittest.TestCase):
    def test_login_returns_account(self):
        session = Mock()
        session.post.return_value = _json_response({"accountId": "acct-1", "accountHash": "hsh-1"})
        account = login_rossmann_account(session, "a@b.de", "secret")
        self.assertEqual(account, RossmannAccount("acct-1", "hsh-1"))
        _, kwargs = session.post.call_args
        self.assertEqual(kwargs["json"], {"email": "a@b.de", "password": "secret"})
        headers = kwargs["headers"]
        self.assertEqual(headers["x-api-key"], RossmannConfig.X_API_KEY)
        self.assertEqual(headers["Accept"], "*/*")
        self.assertEqual(headers["App-Version"], "5.11.1")
        self.assertEqual(headers["Build-Number"], "421000110")
        self.assertEqual(headers["Platform"], "android")
        self.assertEqual(headers["Platform-Version"], "14")
        self.assertEqual(headers["Build-Serial"], "unknown")
        self.assertEqual(UUID(headers["X-Correlation-Id"]).version, 4)

    def test_login_raises_on_missing_account(self):
        session = Mock()
        session.post.return_value = _json_response({})
        with self.assertRaises(RossmannAuthError):
            login_rossmann_account(session, "a@b.de", "secret")

    def test_login_raises_on_non_200(self):
        session = Mock()
        session.post.return_value = _json_response({}, status_code=403)
        with self.assertRaises(RossmannAuthError):
            login_rossmann_account(session, "a@b.de", "secret")


class MintAnybillTokenTests(unittest.TestCase):
    def test_mint_returns_token(self):
        session = Mock()
        session.get.return_value = _json_response({"accessToken": "any-tok"})
        account = RossmannAccount("acct-1", "hsh-1")
        token = mint_anybill_token(session, account)
        self.assertEqual(token, "any-tok")
        _, kwargs = session.get.call_args
        headers = kwargs["headers"]
        self.assertEqual(headers["Account-Hash"], "hsh-1")
        self.assertEqual(headers["x-api-key"], RossmannConfig.X_API_KEY)
        self.assertEqual(headers["Platform"], "android")
        self.assertEqual(UUID(headers["X-Correlation-Id"]).version, 4)

    def test_mint_raises_on_missing_token(self):
        session = Mock()
        session.get.return_value = _json_response({"refreshToken": "x"})
        with self.assertRaises(RossmannAuthError):
            mint_anybill_token(session, RossmannAccount("a", "h"))

    def test_mint_raises_on_non_200(self):
        session = Mock()
        session.get.return_value = _json_response({}, status_code=403)
        with self.assertRaises(RossmannAuthError):
            mint_anybill_token(session, RossmannAccount("a", "h"))


class BuildAnybillApiSessionTests(unittest.TestCase):
    def test_sets_bearer_header(self):
        cookie_session = Mock()
        with patch("auth.rossmann_auth.mint_anybill_token", return_value="tok-abc"):
            api_session = build_anybill_api_session(cookie_session, RossmannAccount("a", "h"))
        self.assertEqual(api_session.headers["Authorization"], "Bearer tok-abc")


class AnybillTokenRefresherTests(unittest.TestCase):
    def test_refresher_returns_token_on_success(self):
        cookie_session = Mock()
        account = RossmannAccount("a", "h")
        refresher = make_anybill_token_refresher(cookie_session, account)
        with patch("auth.rossmann_auth.mint_anybill_token", return_value="tok-new"):
            self.assertEqual(refresher(), "tok-new")

    def test_refresher_returns_none_on_error(self):
        cookie_session = Mock()
        account = RossmannAccount("a", "h")
        refresher = make_anybill_token_refresher(cookie_session, account)
        with patch(
            "auth.rossmann_auth.mint_anybill_token",
            side_effect=RossmannAuthError("bad"),
        ):
            self.assertIsNone(refresher())


class PromptRossmannLoginTests(unittest.TestCase):
    def test_login_prompts_and_returns_account(self):
        with patch("builtins.input", return_value="a@b.de"), patch(
            "getpass.getpass", return_value="secret"
        ), patch(
            "auth.rossmann_auth.login_rossmann_account",
            return_value=RossmannAccount("acct-1", "hsh-1"),
        ) as login:
            account = prompt_rossmann_login()
        self.assertEqual(account, RossmannAccount("acct-1", "hsh-1"))
        login.assert_called_once()
        self.assertEqual(login.call_args.args[1], "a@b.de")

    def test_aborts_on_empty_email(self):
        with patch("builtins.input", return_value=""):
            self.assertIsNone(prompt_rossmann_login())

    def test_returns_none_on_login_error(self):
        with patch("builtins.input", return_value="a@b.de"), patch(
            "getpass.getpass", return_value="secret"
        ), patch(
            "auth.rossmann_auth.login_rossmann_account",
            side_effect=RossmannAuthError("bad"),
        ):
            self.assertIsNone(prompt_rossmann_login())


if __name__ == "__main__":
    unittest.main()
