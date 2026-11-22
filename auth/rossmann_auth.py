"""Rossmann account API token mint and anybill token handling.

Rossmann digital receipts are served by the white-label provider anybill.
The Rossmann app logs into the Rossmann account API to obtain ``accountId``
and ``accountHash``, then calls the receipt-auth endpoint to mint a short-lived
anybill access token. This module implements that flow with ``requests`` only
(per ADR-0006).
"""

from __future__ import annotations

import getpass
import logging
from typing import Callable, NamedTuple
from uuid import uuid4

import requests

from config import RossmannConfig

logger = logging.getLogger(__name__)


class RossmannAuthError(RuntimeError):
    """Raised when the Rossmann/anybill token move cannot be completed."""


class RossmannAccount(NamedTuple):
    """Rossmann account identity needed for the anybill token mint."""

    account_id: str
    account_hash: str


def _account_request_headers() -> dict[str, str]:
    """Build the metadata expected by the Rossmann account API."""
    return {
        "Accept": "*/*",
        "X-Correlation-Id": str(uuid4()),
        "App-Version": RossmannConfig.ACCOUNT_APP_VERSION,
        "Build-Number": RossmannConfig.ACCOUNT_BUILD_NUMBER,
        "Platform": RossmannConfig.ACCOUNT_PLATFORM,
        "Platform-Version": RossmannConfig.ACCOUNT_PLATFORM_VERSION,
        "Build-Serial": RossmannConfig.ACCOUNT_BUILD_SERIAL,
        RossmannConfig.X_API_KEY_HEADER: RossmannConfig.X_API_KEY,
    }


def login_rossmann_account(
    session: requests.Session,
    email: str,
    password: str,
    anonymous_account_hash: str = "",
    anonymous_account_id: str = "",
) -> RossmannAccount:
    """Log in to the Rossmann account API and return the account identity.

    ``POST accounts/login`` accepts a ``LoginRequestDto`` with optional
    anonymous account fields plus email/password, and returns
    ``accountHash``/``accountId`` on success. Requires credentials; used only
    when no session cookie exists that already resolves an account.
    """
    payload = {
        "email": email,
        "password": password,
    }
    if anonymous_account_hash:
        payload["anonymousAccountHash"] = anonymous_account_hash
    if anonymous_account_id:
        payload["anonymousAccountId"] = anonymous_account_id

    try:
        response = session.post(
            RossmannConfig.get_account_login_url(),
            json=payload,
            headers=_account_request_headers(),
            timeout=RossmannConfig.DEFAULT_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise RossmannAuthError(f"Rossmann-Login fehlgeschlagen: {exc}") from exc

    if response.status_code != 200:
        raise RossmannAuthError(
            f"Rossmann-Login-Endpoint antwortete mit HTTP {response.status_code}."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RossmannAuthError("Rossmann-Login-Antwort ist kein gültiges JSON.") from exc

    account_id = _optional_text(data.get("accountId"))
    account_hash = _optional_text(data.get("accountHash"))
    if not account_id or not account_hash:
        raise RossmannAuthError(
            "Rossmann-Login lieferte keine accountId/accountHash."
        )
    return RossmannAccount(account_id=account_id, account_hash=account_hash)


def mint_anybill_token(
    session: requests.Session,
    account: RossmannAccount,
) -> str:
    """Mint a fresh anybill access token from the Rossmann account API.

    ``GET /accounts/{accountId}/receipt/auth`` with the ``Account-Hash``
    header returns ``AnybillTokenResultDto { accessToken, ... }``.
    """
    url = RossmannConfig.get_receipt_auth_url(account.account_id)
    try:
        response = session.get(
            url,
            headers={
                **_account_request_headers(),
                RossmannConfig.ACCOUNT_HASH_HEADER: account.account_hash,
            },
            timeout=RossmannConfig.DEFAULT_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise RossmannAuthError(f"Rossmann-Token-Mint fehlgeschlagen: {exc}") from exc

    if response.status_code != 200:
        raise RossmannAuthError(
            f"Rossmann receipt/auth antwortete mit HTTP {response.status_code}."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RossmannAuthError("Rossmann receipt/auth ist kein gültiges JSON.") from exc

    access_token = _optional_text(data.get("accessToken"))
    if not access_token:
        raise RossmannAuthError(
            "Rossmann receipt/auth lieferte keinen anybill accessToken."
        )
    return access_token


def build_anybill_api_session(
    cookie_session: requests.Session,
    account: RossmannAccount,
) -> requests.Session:
    """Build a fresh anybill API session carrying the any bill bearer token.

    The returned session is used for the anybill App API v4 calls.
    """
    token = mint_anybill_token(cookie_session, account)
    api_session = requests.Session()
    api_session.headers.update(
        {
            "User-Agent": RossmannConfig.DEFAULT_USER_AGENT,
            "Authorization": f"{RossmannConfig.ANYBILL_TOKEN_PREFIX}{token}",
        }
    )
    return api_session


def refresh_anybill_token(
    api_session: requests.Session,
    refresh_token: str,
) -> str | None:
    """Refresh an expired anybill token via ``POST authentication/refresh``.

    Returns the new access token or ``None`` on failure.
    """
    payload = {"refreshToken": refresh_token}
    try:
        response = api_session.post(
            RossmannConfig.get_anybill_refresh_url(),
            json=payload,
            timeout=RossmannConfig.DEFAULT_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("✗ anybill-Refresh fehlgeschlagen: %s", exc)
        return None

    if response.status_code != 200:
        logger.error("✗ anybill-Refresh antwortete mit HTTP %s", response.status_code)
        return None

    try:
        data = response.json()
    except ValueError:
        return None

    new_token = _optional_text(data.get("accessToken"))
    if new_token:
        api_session.headers["Authorization"] = (
            f"{RossmannConfig.ANYBILL_TOKEN_PREFIX}{new_token}"
        )
    return new_token


def make_anybill_token_refresher(
    cookie_session: requests.Session,
    account: RossmannAccount,
) -> Callable[[], str | None]:
    """Return a callable that mints a fresh anybill token from the Rossmann account.

    On 401 the client re-mints the token via ``receipt/auth`` and retries once.
    """

    def refresh() -> str | None:
        try:
            return mint_anybill_token(cookie_session, account)
        except RossmannAuthError as exc:  # pragma: no cover - error path
            logger.error("✗ anybill-Token-Refresh fehlgeschlagen: %s", exc)
            return None

    return refresh


def authenticate_rossmann_account(email: str, password: str) -> RossmannAccount:
    """Log in with credentials supplied for a single import."""
    with requests.Session() as session:
        session.headers["User-Agent"] = RossmannConfig.DEFAULT_USER_AGENT
        return login_rossmann_account(session, email, password)


def prompt_rossmann_login() -> RossmannAccount | None:
    """Interactively ask for Rossmann account credentials and log in.

    Credentials are only read at runtime (``input`` / ``getpass``) and are
    never stored. Returns ``None`` when the user aborts or the login fails.
    """
    email = input("Rossmann-Konto-E-Mail: ").strip()
    if not email:
        return None
    password = getpass.getpass("Rossmann-Konto-Passwort: ")
    if not password:
        return None

    try:
        return authenticate_rossmann_account(email, password)
    except RossmannAuthError as exc:
        logger.error("✗ %s", exc)
        return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
