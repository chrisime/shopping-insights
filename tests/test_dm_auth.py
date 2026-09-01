import unittest
from unittest.mock import Mock, patch

import requests

from auth.dm_auth import (
    DmAuthError,
    acquire_dm_access_token,
    build_dm_api_session,
    generate_pkce_pair,
    make_dm_token_refresher,
)


class DmAuthPkceTests(unittest.TestCase):
    def test_generate_pkce_pair_returns_verifier_and_challenge(self):
        verifier, challenge = generate_pkce_pair()
        self.assertTrue(verifier)
        self.assertTrue(challenge)
        self.assertNotIn("=", verifier)
        self.assertNotIn("=", challenge)

    def test_pkce_pair_is_random(self):
        pair_one = generate_pkce_pair()
        pair_two = generate_pkce_pair()
        self.assertNotEqual(pair_one, pair_two)

    def test_acquire_access_token_returns_token_from_code_flow(self):
        session = Mock()
        auth_response = Mock()
        auth_response.url = "https://account.dm.de/callback?code=the-code&state=x"
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {"access_token": "tok-123"}
        session.get.return_value = auth_response
        session.post.return_value = token_response

        token = acquire_dm_access_token(session)

        self.assertEqual(token, "tok-123")
        session.post.assert_called_once()

    def test_acquire_posts_login_form_when_landing_on_login_page(self):
        """The dm flow requires a second POST with the login form's token+state."""
        session = Mock()
        login_response = Mock()
        login_response.url = "https://signin.dm.de/dm-de/authentication?resumePath=%2Fdm-de%2Foauth-authorize"
        login_response.text = (
            '<form id="form1" action="/dm-de/oauth-authorize" method="post">'
            '<input type="hidden" name="token" value="csrf-token-123"/>'
            '<input type="hidden" name="state" value="state-456"/>'
            "</form>"
        )
        callback_response = Mock()
        callback_response.url = "https://account.dm.de/callback?code=code-from-form&state=state-456"
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {"access_token": "tok-789"}
        session.get.return_value = login_response
        session.post.side_effect = [callback_response, token_response]

        token = acquire_dm_access_token(session)

        self.assertEqual(token, "tok-789")
        post_calls = session.post.call_args_list
        self.assertEqual(len(post_calls), 2)
        first_post_url = post_calls[0].args[0]
        self.assertIn("/dm-de/oauth-authorize", first_post_url)
        first_post_data = post_calls[0].kwargs["data"]
        self.assertEqual(first_post_data["token"], "csrf-token-123")
        self.assertEqual(first_post_data["state"], "state-456")

    def test_acquire_raises_when_login_form_has_no_code(self):
        """A login page without a usable form must still raise DmAuthError."""
        session = Mock()
        login_response = Mock()
        login_response.url = "https://signin.dm.de/dm-de/authentication?resumePath=%2Fdm-de%2Foauth-authorize"
        login_response.text = "<html><title>dm Login</title></html>"
        session.get.return_value = login_response

        with self.assertRaises(DmAuthError):
            acquire_dm_access_token(session)

    def test_acquire_raises_when_no_code_received(self):
        session = Mock()
        auth_response = Mock()
        auth_response.url = "https://signin.dm.de/dm-de/authentication?error=login_required"
        auth_response.text = "<html><title>dm Login</title></html>"
        session.get.return_value = auth_response

        with self.assertRaises(DmAuthError):
            acquire_dm_access_token(session)

    def test_acquire_raises_when_token_missing(self):
        session = Mock()
        auth_response = Mock()
        auth_response.url = "https://account.dm.de/callback?code=the-code&state=x"
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {"id_token": "only-id"}
        session.get.return_value = auth_response
        session.post.return_value = token_response

        with self.assertRaises(DmAuthError):
            acquire_dm_access_token(session)

    def test_acquire_raises_on_token_endpoint_error(self):
        session = Mock()
        auth_response = Mock()
        auth_response.url = "https://account.dm.de/callback?code=the-code&state=x"
        token_response = Mock()
        token_response.status_code = 400
        session.get.return_value = auth_response
        session.post.return_value = token_response

        with self.assertRaises(DmAuthError):
            acquire_dm_access_token(session)

    def test_acquire_raises_on_network_error(self):
        session = Mock()
        session.get.side_effect = requests.exceptions.ConnectionError("down")

        with self.assertRaises(DmAuthError):
            acquire_dm_access_token(session)

    def test_build_dm_api_session_sets_bearer_header(self):
        cookie_session = Mock()
        with patch("auth.dm_auth.acquire_dm_access_token", return_value="tok-abc"):
            api_session = build_dm_api_session(cookie_session)

        self.assertEqual(api_session.headers["Authorization"], "Bearer tok-abc")
        self.assertEqual(api_session.headers["Src"], "web")

    def test_token_refresher_returns_none_on_error(self):
        cookie_session = Mock()
        refresher = make_dm_token_refresher(cookie_session)
        with patch(
            "auth.dm_auth.acquire_dm_access_token",
            side_effect=DmAuthError("invalid session"),
        ):
            self.assertIsNone(refresher())

    def test_token_refresher_returns_token_on_success(self):
        cookie_session = Mock()
        refresher = make_dm_token_refresher(cookie_session)
        with patch("auth.dm_auth.acquire_dm_access_token", return_value="tok-xyz"):
            self.assertEqual(refresher(), "tok-xyz")


if __name__ == "__main__":
    unittest.main()