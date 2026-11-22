"""File-based cookie loading and diagnostics for Rossmann sessions.

Rossmann authenticates through the Rossmann account API to mint an anybill
token (ADR-0006). The exported cookies only serve as the *session* that the
account API accepts; this module loads the cookie file into a session and
assesses whether the export is likely sufficient.
"""

from __future__ import annotations

import logging
import os
import json

logger = logging.getLogger(__name__)

import requests

from config import RossmannConfig

from .cookie_diagnostics import (
    CookieDiagnosticExtras,
    CookieDiagnosticProfile,
    print_cookie_diagnostics,
)
from .cookie_policies import ROSSMANN_SESSION_COOKIE_PREFIXES
from .shared_file_auth import (
    build_cookie_session,
    parse_json_cookie_export,
    read_utf8_text_file,
)


DEFAULT_ROSSMANN_COOKIE_DOMAIN = f".{RossmannConfig.get_cookie_domain()}"


def read_rossmann_account(raw_cookie_text: str) -> dict[str, str] | None:
    """Read Rossmann ``accountId``/``accountHash`` embedded in a JSON export.

    The Rossmann web session does not directly map to an anybill account.
    A Rossmann cookie/request file may carry top-level ``accountId`` and
    ``accountHash`` fields (as exported by the Rossmann app account state);
    this helper extracts them for the anybill token mint.
    """
    stripped = raw_cookie_text.strip()
    if not stripped:
        return None
    try:
        data = json.loads(stripped)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    account_id = str(data.get("accountId") or "").strip()
    account_hash = str(data.get("accountHash") or "").strip()
    if account_id and account_hash:
        return {"accountId": account_id, "accountHash": account_hash}
    return None


def _rossmann_has_session_cookie(cookie_names: set[str]) -> bool:
    return any(
        name.startswith(ROSSMANN_SESSION_COOKIE_PREFIXES) for name in cookie_names
    )


def _classify_rossmann_cookie_quality(cookie_names: set[str]) -> str:
    if not cookie_names:
        return "ROT"
    if not _rossmann_has_session_cookie(cookie_names):
        return "GELB"
    return "GRUEN"


def _build_rossmann_diagnostic_profile(cookie_names: set[str]) -> CookieDiagnosticProfile:
    recommended = {
        name for name in cookie_names if name.startswith(ROSSMANN_SESSION_COOKIE_PREFIXES)
    }
    return CookieDiagnosticProfile(
        store_name="Rossmann",
        required_cookies=set(cookie_names),
        recommended_cookies=recommended,
        rot_summary="keine Rossmann-Cookies vorhanden",
        rot_recommendation="Exportiere die Cookies nach einem funktionierenden Aufruf von www.rossmann.de erneut. Ohne eine Rossmann-Session ist kein anybill-Token-Mint möglich.",
        rot_relogin_step="Melde dich in einem regulaeren Browser bei www.rossmann.de (oder in der App) an und exportiere die Cookies danach erneut.",
        rot_missing_hint="Ohne Rossmann-Session-Cookies ist der anybill-Token-Mint nicht möglich.",
        gelb_recommendation="Es gibt Rossmann-Cookies, aber keine erkennbare Session. Die Gültigkeit wird beim Live-Token-Check geprüft.",
        gelb_missing_hint="",
        gelb_try_step="Du kannst den Abruf probieren. Wenn es hakt, exportiere die Cookies nach einem funktionierenden Rossmann-Aufruf erneut.",
        gruen_recommendation="Die Rossmann-Cookies wirken ausreichend. Du kannst den Abruf mit --cookies-file starten.",
        gruen_step="Die Datei wirkt ausreichend. Du kannst den Rossmann-Abruf voraussichtlich direkt mit --cookies-file starten.",
        missing_required_hint="Ohne Rossmann-Cookies ist der anybill-Token-Mint nicht möglich.",
    )


def _print_rossmann_cookie_diagnostics(session: requests.Session) -> None:
    cookie_names = {cookie.name for cookie in session.cookies}
    profile = _build_rossmann_diagnostic_profile(cookie_names)
    status = _classify_rossmann_cookie_quality(cookie_names)
    print_cookie_diagnostics(session.cookies, profile)
    logger.info("  Ampelstatus: %s", status)


def _build_rossmann_cookie_session_from_text(
    raw_cookie_text: str,
) -> tuple[requests.Session, int] | None:
    cookies_list = _parse_cookie_file(raw_cookie_text)
    if not cookies_list:
        return None
    return build_cookie_session(
        cookies_list,
        user_agent=RossmannConfig.DEFAULT_USER_AGENT,
        domain_suffix=None,
    )


def _parse_cookie_session_payload(
    raw_cookie_text: str,
    invalid_format_message: str,
) -> tuple[requests.Session, int] | None:
    session_payload = _build_rossmann_cookie_session_from_text(raw_cookie_text)
    if session_payload is None:
        logger.error(invalid_format_message)
        return None

    session, cookie_count = session_payload
    if cookie_count == 0:
        logger.error("✗ Keine Rossmann-Cookies in der Datei gefunden.")
        return None

    return session, cookie_count


def load_rossmann_cookies_from_file(
    file_path: str | None = None,
) -> requests.Session | None:
    """Load Rossmann cookies from a file into a requests session."""
    if file_path is None:
        file_path = RossmannConfig.COOKIES_JSON_FILE

    logger.info("Lade Rossmann-Cookies aus Datei: %s...", file_path)

    try:
        if not os.path.exists(file_path):
            logger.error("✗ Cookie-Datei nicht gefunden: %s", file_path)
            return None

        raw_cookie_text = read_utf8_text_file(file_path)
        session_payload = _parse_cookie_session_payload(
            raw_cookie_text,
            "✗ Ungültiges Cookie-Dateiformat. Unterstützt werden JSON, Netscape, rohe Cookie-Header und komplette Request-Header.",
        )
        if session_payload is None:
            return None

        session, cookie_count = session_payload
        logger.info("✓ Erfolgreich %d Rossmann-Cookies geladen", cookie_count)
        _print_rossmann_cookie_diagnostics(session)
        return session

    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("✗ Fehler beim Laden der Rossmann-Cookies: %s", exc)
        return None


def diagnose_rossmann_cookie_file(file_path: str | None = None) -> bool:
    """Analyze a Rossmann cookie/request file and print actionable diagnostics."""
    if file_path is None:
        file_path = RossmannConfig.COOKIES_JSON_FILE

    logger.info("Prüfe Rossmann-Cookie-Datei: %s...", file_path)

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
        "✗ Datei konnte nicht als Rossmann-Cookie-/Request-Datei erkannt werden.",
    )
    if session_payload is None:
        return False

    session, cookie_count = session_payload
    logger.info("✓ Datei ist lesbar, %d Rossmann-Cookies erkannt", cookie_count)
    _print_rossmann_cookie_diagnostics(session)

    cookie_names = {cookie.name for cookie in session.cookies}
    return _classify_rossmann_cookie_quality(cookie_names) != "ROT"


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
                "domain": DEFAULT_ROSSMANN_COOKIE_DOMAIN,
                "path": "/",
                "secure": False,
                "expirationDate": None,
                "name": morsel.key,
                "value": morsel.value,
            }
        )

    return cookies


diagnose_rossmann_cookie_file.__test__ = False  # type: ignore[attr-defined]