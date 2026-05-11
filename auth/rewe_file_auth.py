"""File-based cookie loading for REWE authentication."""

import os
from http.cookies import SimpleCookie
from typing import List, Optional, Set

import requests

from config import ReweConfig

from .cookie_policies import (
    IMPORTANT_REWE_COOKIE_NAMES,
    REQUIRED_REWE_COOKIE_NAMES,
    RECOMMENDED_REWE_WAF_COOKIE_NAMES,
)
from .rewe_customer_id import extract_rewe_customer_id_from_text
from .shared_file_auth import (
    CookieDiagnosticProfile,
    assess_cookie_quality,
    build_cookie_session,
    parse_json_cookie_export,
    print_cookie_diagnostics,
    read_utf8_text_file,
)


DEFAULT_REWE_COOKIE_DOMAIN = f".{ReweConfig.get_cookie_domain()}" #".rewe.de"

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


def _rewe_extra_diagnostics_factory(raw_cookie_text: str):
    """Return a callback that prints REWE-specific extra diagnostics."""
    def _extra(cookie_names: Set[str]) -> None:
        missing_waf = sorted(RECOMMENDED_REWE_WAF_COOKIE_NAMES - cookie_names)
        if missing_waf:
            print(
                f"ℹ Optionale WAF-/Cloudflare-Cookies fehlen: {', '.join(missing_waf)}"
            )
            print("  Das ist nach aktueller Praxiserfahrung nicht zwingend problematisch.")

        customer_id = extract_rewe_customer_id_from_text(raw_cookie_text)
        if customer_id:
            print(f"✓ customerId in der Datei erkannt: {customer_id}")
        else:
            print(
                "ℹ Keine customerId direkt in der Datei erkannt. Das ist bei reinen Cookie-Dateien normal."
            )
    return _extra


def _rewe_extra_steps_factory(raw_cookie_text: str):
    """Return a callback that provides REWE-specific next-step texts."""
    def _steps(status: str, cookie_names: Set[str]) -> List[str]:
        steps: List[str] = []
        if status == "GELB":
            missing_waf = sorted(RECOMMENDED_REWE_WAF_COOKIE_NAMES - cookie_names)
            if missing_waf:
                steps.append(
                    f"Optionale WAF-/Cloudflare-Cookies ({', '.join(missing_waf)}) fehlen zwar, sind aber nach aktueller Erfahrung nicht der Hauptfaktor."
                )
        customer_id = extract_rewe_customer_id_from_text(raw_cookie_text)
        if not customer_id:
            steps.append(
                "Fehlende customerId in einer reinen Cookie-Datei ist normal. Zuerst Session-/couponwallet-Aufloesung probieren; nur bei Bedarf spaeter --customer-id manuell setzen."
            )
        return steps
    return _steps


def _looks_like_rewe_domain(domain: str) -> bool:
    """Return True when a cookie domain belongs to REWE."""
    if not domain:
        return False
    normalized = domain.lower().lstrip(".")
    return normalized.endswith("rewe.de")


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

    print(f"Lade REWE-Cookies aus Datei: {file_path}...")

    try:
        if not os.path.exists(file_path):
            print(f"✗ Cookie-Datei nicht gefunden: {file_path}")
            print(
                "Bitte übergib eine REWE-Cookie-Datei oder einen kopierten Request-/Header-Export an den REWE-POC."
            )
            return None

        raw_cookie_text = read_utf8_text_file(file_path)

        session_payload = _build_rewe_cookie_session_from_text(raw_cookie_text)
        if session_payload is None:
            print(
                "✗ Ungültiges Cookie-Dateiformat. Unterstützt werden JSON, Netscape-Cookie-Dateien, rohe Cookie-Header und komplette Request-Header mit Cookie-Zeile."
            )
            return None

        session, cookie_count = session_payload

        if cookie_count == 0:
            print("✗ Keine Cookies für rewe.de in der Datei gefunden.")
            return None

        print(f"✓ Erfolgreich {cookie_count} REWE-Cookies geladen")
        profile = _rewe_diagnostic_profile()
        print_cookie_diagnostics(
            session.cookies,
            profile,
            extra_diagnostics=_rewe_extra_diagnostics_factory(raw_cookie_text),
            extra_steps=_rewe_extra_steps_factory(raw_cookie_text),
        )
        return session

    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"✗ Fehler beim Laden der REWE-Cookies: {exc}")
        return None


def diagnose_rewe_cookie_file(file_path: Optional[str] = None) -> bool:
    """Analyze a REWE cookie/request file and print actionable diagnostics."""
    if file_path is None:
        file_path = ReweConfig.REWE_COOKIES_JSON_FILE

    print(f"Prüfe REWE-Cookie-Datei: {file_path}...")

    if not file_path or not os.path.exists(file_path):
        print(f"✗ Datei nicht gefunden: {file_path}")
        return False

    try:
        raw_cookie_text = read_utf8_text_file(file_path)
    except Exception as exc:  # pragma: no cover - filesystem dependent
        print(f"✗ Datei konnte nicht gelesen werden: {exc}")
        return False

    session_payload = _build_rewe_cookie_session_from_text(raw_cookie_text)
    if session_payload is None:
        print(
            "✗ Datei konnte nicht als REWE-Cookie-/Request-Datei erkannt werden. Unterstützt werden JSON, Netscape, rohe Cookie-Header und komplette Request-Header."
        )
        return False

    session, cookie_count = session_payload

    if cookie_count == 0:
        print("✗ Keine REWE-Cookies für rewe.de in der Datei gefunden.")
        return False

    print(f"✓ Datei ist lesbar, {cookie_count} REWE-Cookies erkannt")
    profile = _rewe_diagnostic_profile()
    print_cookie_diagnostics(
        session.cookies,
        profile,
        extra_diagnostics=_rewe_extra_diagnostics_factory(raw_cookie_text),
        extra_steps=_rewe_extra_steps_factory(raw_cookie_text),
    )
    status, _, _ = assess_cookie_quality(
        {cookie.name for cookie in session.cookies}, profile,
    )
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


def _is_valid_rewe_cookie_data(cookie_data: dict) -> bool:
    """Return True for cookie dicts that belong to REWE and have a name."""
    domain = str(cookie_data.get("domain", "") or "")
    name = str(cookie_data.get("name", "") or "")
    return _looks_like_rewe_domain(domain) and bool(name)


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
        include_cookie=_is_valid_rewe_cookie_data,
    )

