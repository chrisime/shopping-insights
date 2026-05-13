"""LIDL-specific file-based cookie loading for authentication."""

import os
from typing import Optional

import requests

from config import LidlConfig

from .cookie_policies import (
    LIDL_IDENTITY_COOKIE_NAMES,
    REQUIRED_LIDL_COOKIE_NAMES,
    RECOMMENDED_LIDL_COOKIE_NAMES,
)
from .shared_file_auth import (
    CookieDiagnosticExtras,
    CookieDiagnosticProfile,
    assess_cookie_quality,
    build_cookie_session,
    parse_json_cookie_export,
    print_cookie_diagnostics,
    read_utf8_text_file,
)


def _lidl_diagnostic_profile() -> CookieDiagnosticProfile:
    """Return the LIDL-specific diagnostic profile."""
    return CookieDiagnosticProfile(
        store_name="LIDL",
        required_cookies=REQUIRED_LIDL_COOKIE_NAMES,
        recommended_cookies=RECOMMENDED_LIDL_COOKIE_NAMES,
        rot_recommendation="Exportiere die Cookies direkt nach einem funktionierenden LIDL-Login erneut. Ohne authToken ist der Bon-Abruf nicht erfolgreich.",
        rot_relogin_step="LIDL im regulaeren Browser erneut oeffnen und einloggen, bis die Seite erfolgreich funktioniert, und die Cookies direkt danach noch einmal exportieren.",
        rot_missing_hint="Ohne {missing} lohnt sich der Bon-Abruf nicht. Pruefe vor dem naechsten Versuch zuerst erneut mit lidl-check.",
        gelb_recommendation="Der Abruf ist moeglich, aber dir fehlen noch hilfreiche LIDL-Zusatzcookies. Wenn moeglich, exportiere die Cookies nach einem funktionierenden LIDL-Login noch einmal.",
        gelb_missing_hint="Dir fehlen noch hilfreiche LIDL-Cookies ({missing}). Wenn moeglich, exportiere nach einem funktionierenden LIDL-Login erneut.",
        gelb_try_step="Du kannst den Abruf probieren. Wenn es hakt, exportiere die Cookies nach einem funktionierenden LIDL-Login erneut und achte besonders auf authToken sowie hilfreiche Cookies wie ldi-customertoken oder XSRF-TOKEN.",
        gruen_recommendation="Du kannst den LIDL-Abruf voraussichtlich direkt mit --cookies-file starten.",
        gruen_step="Die Datei wirkt ausreichend. Du kannst den LIDL-Abruf voraussichtlich direkt mit --cookies-file starten.",
        missing_required_hint="Ohne authToken ist der Bon-Abruf nicht erfolgreich. Exportiere die Cookies möglichst direkt nach einem funktionierenden LIDL-Login erneut.",
    )


def _build_lidl_diagnostic_extras(cookie_names: set[str]) -> CookieDiagnosticExtras:
    """Return optional LIDL-specific diagnostic lines."""
    lines: list[str] = []
    if LIDL_IDENTITY_COOKIE_NAMES & cookie_names and "authToken" not in cookie_names:
        lines.append(
            "  Es wurden zwar typische Lidl-Konto-/Kontext-Cookies gefunden, "
            "aber kein authToken. Das deutet auf eine unvollständige oder "
            "nicht mehr nutzbare Login-Sitzung hin."
        )
    return CookieDiagnosticExtras(lines=lines)


def load_lidl_cookies_from_file(
    file_path: Optional[str] = None,
) -> Optional[requests.Session]:
    """
    Load authentication cookies from a JSON file (e.g., exported from EditThisCookie).

    Args:
        file_path: Path to the cookie JSON file. If None, uses default from config.

    Returns:
        requests.Session: Session with loaded cookies, or None if error
    """
    if file_path is None:
        file_path = LidlConfig.COOKIES_JSON_FILE

    print(f"Lade Cookies aus Datei: {file_path}...")

    try:
        if not os.path.exists(file_path):
            print(f"✗ Cookie-Datei nicht gefunden: {file_path}")
            print(f"\nBitte erstelle eine Datei '{file_path}' mit deinen Cookies.")
            print("Du kannst Cookies exportieren mit Browser-Erweiterungen wie:")
            print("  - EditThisCookie (exportiere als JSON)")
            print("  - Cookie-Editor")
            print("\nDie Datei sollte ein JSON-Array von Cookie-Objekten enthalten.")
            return None

        raw_cookie_text = read_utf8_text_file(file_path)

        cookies_list = parse_json_cookie_export(raw_cookie_text)
        if cookies_list is None:
            print("✗ Fehler beim Parsen der Cookie-Datei: ungültiges JSON")
            print("Bitte stelle sicher, dass die Datei gültiges JSON enthält.")
            return None

        if not cookies_list:
            print("✗ Ungültiges Cookie-Dateiformat. Erwarte ein JSON-Array oder Objekt mit 'cookies'-Feld.")
            return None

        session, cookie_count = build_cookie_session(
            cookies_list,
            user_agent=LidlConfig.DEFAULT_USER_AGENT,
            domain_suffix=LidlConfig.get_cookie_domain(),
        )

        if cookie_count == 0:
            expected_domain = LidlConfig.get_cookie_domain()
            print(f"✗ Keine Cookies für {expected_domain} in der Datei gefunden.")
            return None

        print(f"✓ Erfolgreich {cookie_count} Cookies aus Datei geladen")
        cookie_names = {cookie.name for cookie in session.cookies}
        profile = _lidl_diagnostic_profile()
        print_cookie_diagnostics(
            session.cookies,
            profile,
            extras=_build_lidl_diagnostic_extras(cookie_names),
        )
        status, _, _ = assess_cookie_quality(
            cookie_names, profile,
        )
        if status == "ROT":
            return None
        return session

    except Exception as e:
        print(f"✗ Fehler beim Laden der Cookie-Datei: {e}")
        return None


def diagnose_lidl_cookie_file(file_path: Optional[str] = None) -> bool:
    """Analyze a LIDL cookie file and print actionable diagnostics."""
    if file_path is None:
        file_path = LidlConfig.COOKIES_JSON_FILE

    print(f"Prüfe LIDL-Cookie-Datei: {file_path}...")

    if not file_path or not os.path.exists(file_path):
        print(f"✗ Datei nicht gefunden: {file_path}")
        return False

    try:
        raw_cookie_text = read_utf8_text_file(file_path)
    except Exception as exc:  # pragma: no cover - filesystem dependent
        print(f"✗ Datei konnte nicht gelesen werden: {exc}")
        return False

    cookies_list = parse_json_cookie_export(raw_cookie_text)
    if cookies_list is None:
        print("✗ Datei konnte nicht als LIDL-Cookie-Datei erkannt werden. Erwarte ein JSON-Array oder Objekt mit 'cookies'-Feld.")
        return False

    if not cookies_list:
        print("✗ Ungültiges Cookie-Dateiformat.")
        return False

    session, cookie_count = build_cookie_session(
        cookies_list,
        user_agent=LidlConfig.DEFAULT_USER_AGENT,
        domain_suffix=LidlConfig.get_cookie_domain(),
    )

    if cookie_count == 0:
        expected_domain = LidlConfig.get_cookie_domain()
        print(f"✗ Keine LIDL-Cookies für {expected_domain} in der Datei gefunden.")
        return False

    print(f"✓ Datei ist lesbar, {cookie_count} LIDL-Cookies erkannt")
    cookie_names = {cookie.name for cookie in session.cookies}
    profile = _lidl_diagnostic_profile()
    print_cookie_diagnostics(
        session.cookies,
        profile,
        extras=_build_lidl_diagnostic_extras(cookie_names),
    )
    status, _, _ = assess_cookie_quality(
        cookie_names, profile,
    )
    return status != "ROT"
