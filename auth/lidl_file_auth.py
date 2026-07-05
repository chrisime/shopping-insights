"""LIDL-specific file-based cookie loading for authentication."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

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
from .jwt_expiry import extract_jwt_expiry_epoch, is_jwt_expired


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

    logger.info("Lade Cookies aus Datei: %s...", file_path)

    try:
        if not os.path.exists(file_path):
            logger.error("✗ Cookie-Datei nicht gefunden: %s", file_path)
            logger.info("Bitte erstelle eine Datei '%s' mit deinen Cookies.", file_path)
            logger.info("Du kannst Cookies exportieren mit Browser-Erweiterungen wie:")
            logger.info("  - EditThisCookie (exportiere als JSON)")
            logger.info("  - Cookie-Editor")
            logger.info("Die Datei sollte ein JSON-Array von Cookie-Objekten enthalten.")
            return None

        raw_cookie_text = read_utf8_text_file(file_path)

        cookies_list = parse_json_cookie_export(raw_cookie_text)
        if cookies_list is None:
            logger.error("✗ Fehler beim Parsen der Cookie-Datei: ungültiges JSON")
            logger.info("Bitte stelle sicher, dass die Datei gültiges JSON enthält.")
            return None

        if not cookies_list:
            logger.error("✗ Ungültiges Cookie-Dateiformat. Erwarte ein JSON-Array oder Objekt mit 'cookies'-Feld.")
            return None

        session, cookie_count = build_cookie_session(
            cookies_list,
            user_agent=LidlConfig.DEFAULT_USER_AGENT,
            domain_suffix=LidlConfig.get_cookie_domain(),
        )

        if cookie_count == 0:
            expected_domain = LidlConfig.get_cookie_domain()
            logger.error("✗ Keine Cookies für %s in der Datei gefunden.", expected_domain)
            return None

        logger.info("✓ Erfolgreich %d Cookies aus Datei geladen", cookie_count)
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

        expiry_epoch = extract_jwt_expiry_epoch(session.cookies, "authToken")
        if expiry_epoch is not None and is_jwt_expired(expiry_epoch):
            logger.error("✗ Das LIDL authToken ist abgelaufen. Bitte Cookies nach erneutem Login neu exportieren.")
            return None

        return session

    except Exception as e:
        logger.error("✗ Fehler beim Laden der Cookie-Datei: %s", e)
        return None


def diagnose_lidl_cookie_file(file_path: Optional[str] = None) -> bool:
    """Analyze a LIDL cookie file and print actionable diagnostics."""
    if file_path is None:
        file_path = LidlConfig.COOKIES_JSON_FILE

    logger.info("Prüfe LIDL-Cookie-Datei: %s...", file_path)

    if not file_path or not os.path.exists(file_path):
        logger.error("✗ Datei nicht gefunden: %s", file_path)
        return False

    try:
        raw_cookie_text = read_utf8_text_file(file_path)
    except Exception as exc:  # pragma: no cover - filesystem dependent
        logger.error("✗ Datei konnte nicht gelesen werden: %s", exc)
        return False

    cookies_list = parse_json_cookie_export(raw_cookie_text)
    if cookies_list is None:
        logger.error("✗ Datei konnte nicht als LIDL-Cookie-Datei erkannt werden.")
        return False

    if not cookies_list:
        logger.error("✗ Ungültiges Cookie-Dateiformat.")
        return False

    session, cookie_count = build_cookie_session(
        cookies_list,
        user_agent=LidlConfig.DEFAULT_USER_AGENT,
        domain_suffix=LidlConfig.get_cookie_domain(),
    )

    if cookie_count == 0:
        expected_domain = LidlConfig.get_cookie_domain()
        logger.error("✗ Keine LIDL-Cookies für %s in der Datei gefunden.", expected_domain)
        return False

    logger.info("✓ Datei ist lesbar, %d LIDL-Cookies erkannt", cookie_count)
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
    expiry_epoch = extract_jwt_expiry_epoch(session.cookies, "authToken")
    if expiry_epoch is not None and is_jwt_expired(expiry_epoch):
        logger.error("✗ Das LIDL authToken ist abgelaufen. Bitte Cookies nach erneutem Login neu exportieren.")
        return False

    return status != "ROT"
