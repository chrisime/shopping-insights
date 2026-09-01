"""dm OAuth 2.0 authorization-code + PKCE authentication.

dm access tokens expire after roughly two and a half minutes, so every run
must mint a fresh token from the user's dm session (browser cookies or a
cookies-file export) via the OAuth authorization-code flow with PKCE. This
module implements that flow with the standard library only (``secrets``,
``hashlib``, ``base64``), following ADR-0005.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlsplit

import requests

from config import DmConfig

logger = logging.getLogger(__name__)


class DmAuthError(RuntimeError):
    """Raised when the dm OAuth flow cannot produce an access token."""


def generate_pkce_pair() -> tuple[str, str]:
    """Return a (code_verifier, code_challenge) pair for PKCE (S256)."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = _code_challenge_for_verifier(verifier)
    return verifier, challenge


def _code_challenge_for_verifier(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _build_authorize_url(state: str, nonce: str, code_challenge: str) -> str:
    """Build the OAuth authorization URL for the dm issuer."""
    params = {
        "response_type": "code",
        "client_id": DmConfig.OAUTH_CLIENT_ID,
        "redirect_uri": DmConfig.OAUTH_REDIRECT_URI,
        "scope": DmConfig.OAUTH_SCOPES,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{DmConfig.get_authorize_url()}?{urlencode(params)}"


def _extract_authorization_code(final_url: str) -> str | None:
    """Read the authorization ``code`` query parameter from the final URL."""
    query = parse_qs(urlsplit(final_url).query)
    return query.get("code", [None])[0]


def _exchange_code_for_token(
    session: requests.Session,
    code: str,
    code_verifier: str,
) -> dict:
    """Exchange the authorization code for token data at the token endpoint."""
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DmConfig.OAUTH_REDIRECT_URI,
        "client_id": DmConfig.OAUTH_CLIENT_ID,
        "code_verifier": code_verifier,
    }
    try:
        response = session.post(
            DmConfig.get_token_url(),
            data=payload,
            timeout=DmConfig.DEFAULT_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise DmAuthError(f"dm-Token-Austausch fehlgeschlagen: {exc}") from exc

    if response.status_code != 200:
        raise DmAuthError(
            f"dm-Token-Endpoint antwortete mit HTTP {response.status_code}."
        )

    try:
        return response.json()
    except ValueError as exc:
        raise DmAuthError("dm-Token-Antwort ist kein gültiges JSON.") from exc


def acquire_dm_access_token(session: requests.Session) -> str:
    """Run the authorization-code + PKCE flow and return a fresh access token.

    ``session`` must carry the dm session cookies (``signin.dm.de`` and/or
    ``.dm.de``). Raises :class:`DmAuthError` when no token can be minted.
    """
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    authorize_url = _build_authorize_url(state, nonce, challenge)

    try:
        response = session.get(
            authorize_url,
            timeout=DmConfig.DEFAULT_TIMEOUT,
            allow_redirects=True,
        )
    except requests.exceptions.RequestException as exc:
        raise DmAuthError(f"dm-Authorize fehlgeschlagen: {exc}") from exc

    code = _extract_authorization_code(response.url)
    if not code:
        # The dm authorize hop lands on an intermediate login page whose
        # form (token + state) the browser submits automatically. Replicate
        # that POST to complete SSO and receive the authorization code.
        code = _submit_login_form(session, response)
    if not code:
        raise DmAuthError(
            "dm-Session ist nicht gültig oder abgelaufen "
            "(kein Authorization-Code erhalten)."
        )

    token_data = _exchange_code_for_token(session, code, verifier)
    access_token = token_data.get("access_token")
    if not access_token:
        raise DmAuthError("dm-Token-Austausch lieferte keinen Access-Token.")
    return access_token


def _submit_login_form(
    session: requests.Session,
    page_response: requests.Response,
) -> str | None:
    """Submit the dm login-page form (token + state) to complete SSO.

    Returns the authorization code when the form submission redirects back to
    the callback with a code, otherwise ``None``.
    """
    token = _extract_hidden_input(page_response.text, "token")
    state = _extract_hidden_input(page_response.text, "state")
    if not token or not state:
        return None

    form_action = _extract_form_action(page_response.text) or DmConfig.OAUTH_AUTHORIZE_PATH
    form_url = f"{DmConfig.OAUTH_BASE_URL}{form_action}"

    try:
        response = session.post(
            form_url,
            data={"token": token, "state": state},
            timeout=DmConfig.DEFAULT_TIMEOUT,
            allow_redirects=True,
        )
    except requests.exceptions.RequestException as exc:
        raise DmAuthError(f"dm-Login-Formular konnte nicht gesendet werden: {exc}") from exc

    return _extract_authorization_code(response.url)


def _extract_hidden_input(html: str, name: str) -> str | None:
    """Extract the value of a hidden ``<input name="...">`` from login HTML."""
    import re

    match = re.search(
        rf'<input[^>]*type="hidden"[^>]*name="{name}"[^>]*value="([^"]*)"',
        html,
    )
    if match:
        return match.group(1)
    # tolerate attribute order where name appears before type
    match = re.search(
        rf'<input[^>]*name="{name}"[^>]*type="hidden"[^>]*value="([^"]*)"',
        html,
    )
    return match.group(1) if match else None


def _extract_form_action(html: str) -> str | None:
    """Extract the ``action`` attribute of the login form."""
    import re

    match = re.search(r'<form[^>]*action="([^"]*)"', html)
    return match.group(1) if match else None


def build_dm_api_session(cookie_session: requests.Session) -> requests.Session:
    """Build a fresh API session carrying a dm bearer token.

    The returned session is used for the purchase-history/eBon API calls and
    carries the ``Authorization: Bearer <token>`` header.
    """
    token = acquire_dm_access_token(cookie_session)
    api_session = requests.Session()
    api_session.headers.update(
        {
            "User-Agent": DmConfig.DEFAULT_USER_AGENT,
            "Authorization": f"Bearer {token}",
            "Src": "web",
        }
    )
    return api_session


def make_dm_token_refresher(
    cookie_session: requests.Session,
) -> Callable[[], str | None]:
    """Return a callable that mints a fresh dm token from the cookie session.

    Returns ``None`` when the session can no longer produce a token so the
    client can surface a clean failure instead of raising.
    """

    def refresh() -> str | None:
        try:
            return acquire_dm_access_token(cookie_session)
        except DmAuthError as exc:  # pragma: no cover - error path
            logger.error("✗ dm-Token-Refresh fehlgeschlagen: %s", exc)
            return None

    return refresh