"""File-based cookie loading for REWE authentication."""

import logging
import os
from http.cookies import SimpleCookie

logger = logging.getLogger(__name__)
from typing import List, Optional, Set

import requests

from config import ReweConfig

from .cookie_policies import (
    IMPORTANT_REWE_COOKIE_NAMES,
    REQUIRED_REWE_COOKIE_NAMES,
    RECOMMENDED_REWE_WAF_COOKIE_NAMES,
)
from .rewe_customer_id import extract_rewe_customer_id_from_text
from .jwt_expiry import extract_jwt_expiry_epoch, is_jwt_expired
from .shared_file_auth import (
    CookieDiagnosticExtras,
    CookieDiagnosticProfile,
    assess_cookie_quality,
    build_cookie_session,
    parse_json_cookie_export,
    print_cookie_diagnostics,
    read_utf8_text_file,
)


DEFAULT_REWE_COOKIE_DOMAIN = f".{ReweConfig.get_cookie_domain()}"

def _rewe_diagnostic_profile() -> CookieDiagnosticProfile:
    """Return the REWE-specific diagnostic profile."""
    return CookieDiagnosticProfile(
        store_name="REWE",
        required_cookies=REQUIRED_REWE_COOKIE_NAMES,
        recommended_cookies=IMPORTANT_REWE_COOKIE_NAMES,
        rot_recommendation="Exportiere die Cookies direkt nach einem funktionierenden REWE-Aufruf erneut. Ohne rstp ist der ZIP-Abruf meist nicht erfolgreich.",
        rot_relogin_step="REWE im regulaeren Browser erneut oeffnen, bis die Seite erfolgreich funktioniert, und die Cookies direkt danach noch einmal exportieren.",
        rot_missing_hint="Ohne {missing} lohnt sich der ZIP-Abruf meist nicht. Pruefe vor dem naechsten Versuch zuerst erneut mit rewe-check.",
        gelb_recommendation="Der Abruf ist moeglich, aber dir fehlen noch hilfreiche REWE-Zusatzcookies. Wenn moeglich, exportiere die Cookies nach einem funktionierenden REWE-Aufruf noch einmal.",
        gelb_missing_hint="Dir fehlen noch hilfreiche REWE-Cookies ({missing}). Wenn moeglich, exportiere nach einem funktionierenden REWE-Aufruf erneut.",
        gelb_try_step="Du kannst den Abruf probieren. Wenn es hakt, exportiere die Cookies nach einem funktionierenden REWE-Aufruf erneut und achte besonders auf rstp sowie hilfreiche REWE-Cookies wie _rdfa oder mtc.",
        gruen_recommendation="Du kannst den REWE-Abruf voraussichtlich direkt mit --cookies-file starten.",
        gruen_step="Die Datei wirkt ausreichend. Du kannst den REWE-Abruf voraussichtlich direkt mit --cookies-file starten.",
        missing_required_hint="Ohne rstp ist der ZIP-Abruf meist nicht erfolgreich. Exportiere die Cookies möglichst direkt nach einem funktionierenden REWE-Aufruf erneut.",
    )
def _build_rewe_diagnostic_extras_for_cookies(
    raw_cookie_text: str,
    cookie_names: Set[str],
    status: str,
) -> CookieDiagnosticExtras:
    """Build REWE-specific diagnostic lines and next steps for the current cookie set."""
    customer_id = extract_rewe_customer_id_from_text(raw_cookie_text)
    missing_waf: List[str] = sorted(
        str(name) for name in (RECOMMENDED_REWE_WAF_COOKIE_NAMES - cookie_names)
    )

    lines: List[str] = []
    if missing_waf:
        lines.append(f"ℹ Optionale WAF-/Cloudflare-Cookies fehlen: {', '.join(missing_waf)}")
        lines.append("  Das ist nach aktueller Praxiserfahrung nicht zwingend problematisch.")

    if customer_id:
        lines.append(f"✓ customerId in der Datei erkannt: {customer_id}")
    else:
        lines.append(
            "ℹ Keine customerId direkt in der Datei erkannt. Das ist bei reinen Cookie-Dateien normal."
        )

    steps: List[str] = []
    if status == "GELB" and missing_waf:
        steps.append(
            f"Optionale WAF-/Cloudflare-Cookies ({', '.join(missing_waf)}) fehlen zwar, sind aber nach aktueller Erfahrung nicht der Hauptfaktor."
        )
    if not customer_id:
        steps.append(
            "Fehlende customerId in einer reinen Cookie-Datei ist normal. Zuerst Session-/couponwallet-Aufloesung probieren; nur bei Bedarf spaeter --customer-id manuell setzen."
        )

    return CookieDiagnosticExtras(lines=lines, steps=steps)


def _print_rewe_cookie_diagnostics(cookies, raw_cookie_text: str) -> None:
    """Print REWE-specific cookie diagnostics for an already parsed cookie jar."""
    profile = _rewe_diagnostic_profile()
    cookie_names = {cookie.name for cookie in cookies}
    status, _, _ = assess_cookie_quality(cookie_names, profile)
    print_cookie_diagnostics(
        cookies,
        profile,
        extras=_build_rewe_diagnostic_extras_for_cookies(
            raw_cookie_text,
            cookie_names,
            status,
        ),
    )


def _parse_rewe_cookie_session_payload(
    raw_cookie_text: str,
    invalid_format_message: str,
) -> Optional[tuple[requests.Session, int]]:
    """Parse raw REWE cookie text and print consistent user-facing errors."""
    session_payload = _build_rewe_cookie_session_from_text(raw_cookie_text)
    if session_payload is None:
        logger.error(invalid_format_message)
        return None

    session, cookie_count = session_payload
    if cookie_count == 0:
        logger.error("✗ Keine REWE-Cookies für rewe.de in der Datei gefunden.")
        return None

    return session, cookie_count


def load_rewe_cookies_from_file(
    file_path: Optional[str] = None,
) -> Optional[requests.Session]:
    """Load REWE cookies from a file into a requests session.

    Supported formats:
    - JSON array of cookie objects
    - JSON object with a top-level ``cookies`` array
    - Netscape cookie file format
    - Raw ``Cookie: name=value; ...`` header text
    - Plain ``name=value`` pairs separated by ``;`` or newlines
    """
    if file_path is None:
        file_path = ReweConfig.REWE_COOKIES_JSON_FILE

    logger.info("Lade REWE-Cookies aus Datei: %s...", file_path)

    try:
        if not os.path.exists(file_path):
            logger.error("✗ Cookie-Datei nicht gefunden: %s", file_path)
            logger.info("Bitte übergib eine REWE-Cookie-Datei oder einen kopierten Request-/Header-Export.")
            return None

        raw_cookie_text = read_utf8_text_file(file_path)

        session_payload = _parse_rewe_cookie_session_payload(
            raw_cookie_text,
            "✗ Ungültiges Cookie-Dateiformat. Unterstützt werden JSON, Netscape-Cookie-Dateien, rohe Cookie-Header und komplette Request-Header mit Cookie-Zeile.",
        )
        if session_payload is None:
            return None

        session, cookie_count = session_payload

        logger.info("✓ Erfolgreich %d REWE-Cookies geladen", cookie_count)
        _print_rewe_cookie_diagnostics(session.cookies, raw_cookie_text)

        expiry_epoch = extract_jwt_expiry_epoch(session.cookies, "rstp")
        if expiry_epoch is not None and is_jwt_expired(expiry_epoch):
            logger.error("✗ Das REWE rstp-Cookie ist abgelaufen. Bitte Cookies nach erneutem Login neu exportieren.")
            return None

        return session

    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("✗ Fehler beim Laden der REWE-Cookies: %s", exc)
        return None


def diagnose_rewe_cookie_file(file_path: Optional[str] = None) -> bool:
    """Analyze a REWE cookie/request file and print actionable diagnostics."""
    if file_path is None:
        file_path = ReweConfig.REWE_COOKIES_JSON_FILE

    logger.info("Prüfe REWE-Cookie-Datei: %s...", file_path)

    if not file_path or not os.path.exists(file_path):
        logger.error("✗ Datei nicht gefunden: %s", file_path)
        return False

    try:
        raw_cookie_text = read_utf8_text_file(file_path)
    except Exception as exc:  # pragma: no cover - filesystem dependent
        logger.error("✗ Datei konnte nicht gelesen werden: %s", exc)
        return False

    session_payload = _parse_rewe_cookie_session_payload(
        raw_cookie_text,
        "✗ Datei konnte nicht als REWE-Cookie-/Request-Datei erkannt werden. Unterstützt werden JSON, Netscape, rohe Cookie-Header und komplette Request-Header.",
    )
    if session_payload is None:
        return False

    session, cookie_count = session_payload

    logger.info("✓ Datei ist lesbar, %d REWE-Cookies erkannt", cookie_count)
    _print_rewe_cookie_diagnostics(session.cookies, raw_cookie_text)
    profile = _rewe_diagnostic_profile()
    status, _, _ = assess_cookie_quality(
        {cookie.name for cookie in session.cookies}, profile,
    )
    expiry_epoch = extract_jwt_expiry_epoch(session.cookies, "rstp")
    if expiry_epoch is not None and is_jwt_expired(expiry_epoch):
        logger.error("✗ Das REWE rstp-Cookie ist abgelaufen. Bitte Cookies nach erneutem Login neu exportieren.")
        return False

    return status != "ROT"


def _parse_cookie_file(raw_cookie_text: str) -> List[dict]:
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


def _parse_netscape_cookies(raw_cookie_text: str) -> List[dict]:
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


def _parse_cookie_header_or_pairs(raw_cookie_text: str) -> List[dict]:
    """Parse raw Cookie headers or simple name=value lists."""
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
                "domain": DEFAULT_REWE_COOKIE_DOMAIN,
                "path": "/",
                "secure": False,
                "expirationDate": None,
                "name": morsel.key,
                "value": morsel.value,
            }
        )

    return cookies


def _build_rewe_cookie_session_from_text(
    raw_cookie_text: str,
) -> Optional[tuple[requests.Session, int]]:
    """Parse raw cookie text and build a REWE session when supported."""
    cookies_list = _parse_cookie_file(raw_cookie_text)
    if not cookies_list:
        return None

    return build_cookie_session(
        cookies_list,
        user_agent=ReweConfig.DEFAULT_USER_AGENT,
        domain_suffix="rewe.de",
    )
