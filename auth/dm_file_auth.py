"""File-based cookie loading and diagnostics for dm OAuth sessions.

dm authenticates through the OAuth 2.0 authorization-code + PKCE flow, so the
exported cookies (``signin.dm.de`` and/or ``.dm.de`` session cookies) only
serve as the *session* that mints short-lived access tokens. This module loads
the cookie file into a session and assesses whether the exported cookie set is
likely sufficient for the OAuth flow.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

import requests

from config import DmConfig

from .cookie_diagnostics import (
    CookieDiagnosticExtras,
    CookieDiagnosticProfile,
    print_cookie_diagnostics,
)
from .cookie_policies import (
    DM_RECOMMENDED_COOKIE_PREFIXES,
    DM_REQUIRED_COOKIE_NAMES,
    DM_REQUIRED_COOKIE_PREFIXES,
)
from .dm_auth import DmAuthError, acquire_dm_access_token
from .shared_file_auth import (
    build_cookie_session,
    parse_json_cookie_export,
    read_utf8_text_file,
)


DEFAULT_DM_COOKIE_DOMAIN = f".{DmConfig.get_cookie_domain()}"


def _dm_has_session_cookie(cookie_names: set[str]) -> bool:
    """Return True when a signin/session cookie is present."""
    return bool(DM_REQUIRED_COOKIE_NAMES & cookie_names) or any(
        name.startswith(DM_REQUIRED_COOKIE_PREFIXES) for name in cookie_names
    )


def _dm_has_recommended_cookie(cookie_names: set[str]) -> bool:
    """Return True when at least one helpful dm cookie is present."""
    return any(
        name.startswith(DM_RECOMMENDED_COOKIE_PREFIXES) for name in cookie_names
    )


def _classify_dm_cookie_quality(cookie_names: set[str]) -> str:
    """Classify the dm cookie set into an operational traffic-light rating."""
    if not _dm_has_session_cookie(cookie_names):
        return "ROT"
    if not _dm_has_recommended_cookie(cookie_names):
        return "GELB"
    return "GRUEN"


def _build_dm_diagnostic_profile(cookie_names: set[str]) -> CookieDiagnosticProfile:
    """Build a dm-specific diagnostic profile for the current cookie set."""
    recommended = {
        name
        for name in cookie_names
        if name.startswith(DM_RECOMMENDED_COOKIE_PREFIXES)
    }
    return CookieDiagnosticProfile(
        store_name="dm",
        required_cookies=set(DM_REQUIRED_COOKIE_NAMES),
        recommended_cookies=recommended,
        rot_summary="dm-Session-Cookies fehlen",
        rot_recommendation="Exportiere die Cookies direkt nach einem funktionierenden dm-Aufruf erneut. Ohne eine signin.dm.de-Session ist der OAuth-Flow nicht möglich.",
        rot_relogin_step="Melde dich in einem regulaeren Browser bei account.dm.de an, bis /purchases funktioniert, und exportiere die Cookies danach erneut.",
        rot_missing_hint="Ohne {missing} ist der dm-OAuth-Flow nicht möglich. Pruefe vor dem naechsten Versuch zuerst erneut mit dm-check.",
        gelb_recommendation="Die Session ist da, aber hilfreiche dm-Cookies fehlen.",
        gelb_missing_hint="Dir fehlen noch hilfreiche dm-Cookies. Wenn moeglich, exportiere die Cookies nach einem funktionierenden dm-Aufruf erneut.",
        gelb_try_step="Du kannst den Abruf probieren. Wenn es hakt, exportiere die Cookies nach einem funktionierenden dm-Aufruf erneut.",
        gruen_recommendation="Die dm-Cookies wirken ausreichend. Du kannst den Abruf voraussichtlich direkt mit --cookies-file starten.",
        gruen_step="Die Datei wirkt ausreichend. Du kannst den dm-Abruf voraussichtlich direkt mit --cookies-file starten.",
        missing_required_hint="Ohne eine signin.dm.de-Session ist der dm-OAuth-Flow nicht möglich. Exportiere die Cookies moeglichst direkt nach einem funktionierenden dm-Aufruf erneut.",
    )


def _print_dm_cookie_diagnostics(session: requests.Session) -> None:
    """Print dm-specific cookie diagnostics for an already parsed session."""
    cookie_names = {cookie.name for cookie in session.cookies}
    profile = _build_dm_diagnostic_profile(cookie_names)
    status = _classify_dm_cookie_quality(cookie_names)
    print_cookie_diagnostics(session.cookies, profile)
    logger.info("  Ampelstatus: %s", status)


def _build_dm_cookie_session_from_text(
    raw_cookie_text: str,
) -> tuple[requests.Session, int] | None:
    """Parse raw cookie text and build a dm session when supported."""
    cookies_list = _parse_cookie_file(raw_cookie_text)
    if not cookies_list:
        return None
    # dm needs cookies from multiple domains (signin.dm.de, .dm.de and
    # optionally *.services.dmtech.com), so no domain-suffix filter is applied.
    return build_cookie_session(
        cookies_list,
        user_agent=DmConfig.DEFAULT_USER_AGENT,
        domain_suffix=None,
    )


def _parse_cookie_session_payload(
    raw_cookie_text: str,
    invalid_format_message: str,
) -> tuple[requests.Session, int] | None:
    """Parse raw dm cookie text and print consistent user-facing errors."""
    session_payload = _build_dm_cookie_session_from_text(raw_cookie_text)
    if session_payload is None:
        logger.error(invalid_format_message)
        return None

    session, cookie_count = session_payload
    if cookie_count == 0:
        logger.error("✗ Keine dm-Cookies in der Datei gefunden.")
        return None

    return session, cookie_count


def load_dm_cookies_from_file(
    file_path: str | None = None,
) -> requests.Session | None:
    """Load dm cookies from a file into a requests session."""
    if file_path is None:
        file_path = DmConfig.COOKIES_JSON_FILE

    logger.info("Lade dm-Cookies aus Datei: %s...", file_path)

    try:
        if not os.path.exists(file_path):
            logger.error("✗ Cookie-Datei nicht gefunden: %s", file_path)
            logger.info("Bitte übergib eine dm-Cookie-Datei oder einen kopierten Request-/Header-Export.")
            return None

        raw_cookie_text = read_utf8_text_file(file_path)

        session_payload = _parse_cookie_session_payload(
            raw_cookie_text,
            "✗ Ungültiges Cookie-Dateiformat. Unterstützt werden JSON, Netscape-Cookie-Dateien, rohe Cookie-Header und komplette Request-Header mit Cookie-Zeile.",
        )
        if session_payload is None:
            return None

        session, cookie_count = session_payload

        logger.info("✓ Erfolgreich %d dm-Cookies geladen", cookie_count)
        _print_dm_cookie_diagnostics(session)

        return session

    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("✗ Fehler beim Laden der dm-Cookies: %s", exc)
        return None


def _attempt_live_token_check(session: requests.Session) -> bool | None:
    """Best-effort OAuth token mint used to confirm the session is live.

    Returns:
        True when a token was minted, False when the session is invalid,
        None when the check could not be performed (e.g. network failure).
    """
    logger.info("Prüfe dm-Session über OAuth (Token-Mint)...")
    try:
        token = acquire_dm_access_token(session)
        if token:
            logger.info("✓ dm-Session gültig – Access-Token erfolgreich ausgestellt.")
            return True
        logger.warning("⚠ dm-Session konnte keinen Access-Token ausstellen.")
        return False
    except DmAuthError as exc:
        logger.warning("✗ dm-Session ungültig: %s", exc)
        return False
    except requests.exceptions.RequestException as exc:  # pragma: no cover - network dependent
        logger.warning("⚠ dm-Session-Check nicht möglich: %s", exc)
        return None


def diagnose_dm_cookie_file(file_path: str | None = None) -> bool:
    """Analyze a dm cookie/request file and print actionable diagnostics."""
    if file_path is None:
        file_path = DmConfig.COOKIES_JSON_FILE

    logger.info("Prüfe dm-Cookie-Datei: %s...", file_path)

    if not file_path or not os.path.exists(file_path):
        logger.error("✗ Datei nicht gefunden: %s", file_path)
        return False

    try:
        raw_cookie_text = read_utf8_text_file(file_path)
    except Exception as exc:  # pragma: no cover - filesystem dependent
        logger.error("✗ Datei konnte nicht gelesen werden: %s", exc)
        return False

    session_payload = _parse_cookie_session_payload(
        raw_cookie_text,
        "✗ Datei konnte nicht als dm-Cookie-/Request-Datei erkannt werden. Unterstützt werden JSON, Netscape, rohe Cookie-Header und komplette Request-Header.",
    )
    if session_payload is None:
        return False

    session, cookie_count = session_payload

    logger.info("✓ Datei ist lesbar, %d dm-Cookies erkannt", cookie_count)
    _print_dm_cookie_diagnostics(session)

    live_result = _attempt_live_token_check(session)
    if live_result is not None:
        return live_result

    cookie_names = {cookie.name for cookie in session.cookies}
    return _classify_dm_cookie_quality(cookie_names) != "ROT"


def _parse_cookie_file(raw_cookie_text: str) -> list[dict]:
    """Parse supported cookie file formats into a normalized cookie list."""
    stripped = raw_cookie_text.strip()
    if not stripped:
        return []

    json_cookies = parse_json_cookie_export(stripped)
    if json_cookies is not None:
        return json_cookies

    netscape_cookies = _parse_netscape_cookies(stripped)
    if netscape_cookies:
        return netscape_cookies

    return _parse_cookie_header_or_pairs(stripped)


def _parse_netscape_cookies(raw_cookie_text: str) -> list[dict]:
    """Parse Netscape cookie files exported by browsers/extensions."""
    cookies = []
    for line in raw_cookie_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split("\t")
        if len(parts) != 7:
            return []

        domain, _, path, secure, expires, name, value = parts
        cookies.append(
            {
                "domain": domain,
                "path": path or "/",
                "secure": secure.upper() == "TRUE",
                "expirationDate": int(expires) if expires.isdigit() else None,
                "name": name,
                "value": value,
            }
        )

    return cookies


def _parse_cookie_header_or_pairs(raw_cookie_text: str) -> list[dict]:
    """Parse raw Cookie headers or simple name=value lists."""
    from http.cookies import SimpleCookie

    normalized = raw_cookie_text.strip()

    if not normalized.lower().startswith("cookie:"):
        for line in normalized.splitlines():
            if line.strip().lower().startswith("cookie:"):
                normalized = line.strip()
                break

    if normalized.lower().startswith("cookie:"):
        normalized = normalized.split(":", 1)[1].strip()

    if "\n" in normalized and ";" not in normalized:
        normalized = "; ".join(
            line.strip() for line in normalized.splitlines() if line.strip()
        )

    simple_cookie = SimpleCookie()
    try:
        simple_cookie.load(normalized)
    except Exception:
        return []

    cookies = []
    for morsel in simple_cookie.values():
        cookies.append(
            {
                "domain": DEFAULT_DM_COOKIE_DOMAIN,
                "path": "/",
                "secure": False,
                "expirationDate": None,
                "name": morsel.key,
                "value": morsel.value,
            }
        )

    return cookies