"""REWE browser cookie extraction (subclass of BrowserCookieExtractor)."""

import logging
from typing import Set

logger = logging.getLogger(__name__)

from config import ReweConfig

from .browser_auth_base import BrowserCookieExtractor
from .cookie_policies import (
    KEYCLOAK_SSO_COOKIE_NAMES,
    REQUIRED_REWE_COOKIE_NAMES,
    RECOMMENDED_REWE_WAF_COOKIE_NAMES,
)
from .jwt_expiry import extract_jwt_expiry_epoch, is_jwt_expired
from .session_cookie_recovery import check_sessionstore_privacy_level, diagnose_session_cookies_for_domain


_SESSION_COOKIE_EXPLANATION = (
    "Das rstp-Cookie ist ein reines Session-Cookie (ohne Ablaufdatum)\n"
    "und wird von Firefox/LibreWolf nur im Arbeitsspeicher gehalten,\n"
    "nicht in cookies.sqlite.\n"
    "Es kann nur aus der Session-Restore-Datei (recovery.jsonlz4)\n"
    "wiederhergestellt werden.\n"
)


class ReweBrowserAuthError(RuntimeError):
    pass


def _looks_like_locked_browser_profile(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        needle in message
        for needle in (
            "database is locked",
            "permission denied",
            "resource busy",
            "file is locked",
            "profile in use",
        )
    )


def _session_cookie_hint(browser_label: str) -> None:
    """Print an actionable hint for Firefox/LibreWolf session-cookie issues.

    Includes a live check of the browser profile's privacy_level setting.
    """
    label = browser_label.lower()
    browser_key = "librewolf" if "librewolf" in label else "firefox"

    privacy_ok = check_sessionstore_privacy_level(browser_key)
    if privacy_ok is False:
        if "librewolf" in label:
            logger.error(
                "  ✗ LibreWolf blockiert Session-Cookies "
                "(browser.sessionstore.privacy_level = 2).\n"
                "    Fix: In about:config den Wert auf 0 setzen,\n"
                "    LibreWolf neu starten und erneut bei REWE anmelden.\n"
                "    Details: docs/LIBREWOLF_SESSION_COOKIES.md"
            )
        else:
            logger.error(
                "  ✗ browser.sessionstore.privacy_level in Firefox ist auf 2\n"
                "    gesetzt – Session-Cookies werden blockiert.\n"
                "    Fix: In about:config den Wert auf 0 oder 1 setzen und\n"
                "    Firefox neu starten."
            )
        return

    if "librewolf" in label:
        logger.info(
            "  LibreWolf blockiert standardmäßig Session-Cookies\n"
            "  (browser.sessionstore.privacy_level = 2).\n"
            "  Fix: In about:config den Wert auf 0 setzen,\n"
            "  LibreWolf neu starten und erneut bei REWE anmelden.\n"
            "  Details: docs/LIBREWOLF_SESSION_COOKIES.md"
        )
    else:
        logger.info(
            "  Firefox muss mindestens einmal ordentlich geschlossen worden\n"
            "  sein, damit die Session-Restore-Datei geschrieben wird.\n"
            "  Dann sollte rstp daraus gelesen werden können.\n"
            "  Prüfe ggf. in about:config ob browser.sessionstore.privacy_level\n"
            "  auf 0 oder 1 gesetzt ist."
        )


def _log_rewe_firefox_session_diagnostics(browser_label: str) -> None:
    diagnostics = diagnose_session_cookies_for_domain("firefox" if "firefox" in browser_label.lower() else "librewolf", ReweConfig.get_cookie_domain())

    if diagnostics.reason == "profiles_dir_missing":
        logger.info("  ✗ Kein lokales %s-Profilverzeichnis gefunden.", browser_label)
    elif diagnostics.reason == "profile_missing":
        logger.info("  ✗ Kein passendes %s-Profil mit Session-Daten gefunden.", browser_label)
    elif diagnostics.reason == "recovery_missing":
        logger.info("  ✗ Im %s-Profil fehlt sessionstore-backups/recovery.jsonlz4.", browser_label)
    elif diagnostics.reason == "recovery_unreadable":
        logger.info("  ✗ sessionstore-backups/recovery.jsonlz4 im %s-Profil ist nicht lesbar.", browser_label)
    elif diagnostics.reason == "recovery_empty":
        logger.info("  ✗ sessionstore-backups/recovery.jsonlz4 enthält keine Session-Cookies.", browser_label)
    elif diagnostics.reason == "no_matching_cookies":
        logger.info("  ✗ recovery.jsonlz4 enthält keine REWE-Cookies für %s.", ReweConfig.get_cookie_domain())
    elif diagnostics.reason == "ok":
        logger.info("  ℹ %d REWE-Session-Cookie(s) für %s im Firefox-Profil gefunden.", diagnostics.matched_cookie_count, ReweConfig.get_cookie_domain())


class ReweBrowserCookieExtractor(BrowserCookieExtractor):
    """Extract REWE session cookies from a local browser profile."""

    retailer_name = "REWE"
    supported_browsers = ReweConfig.SUPPORTED_BROWSERS
    default_user_agent = ReweConfig.DEFAULT_USER_AGENT
    required_cookies = REQUIRED_REWE_COOKIE_NAMES
    recommended_cookies = RECOMMENDED_REWE_WAF_COOKIE_NAMES
    include_expires = True
    filter_by_domain_suffix = True

    @property  # type: ignore[override]
    def cookie_domain(self) -> str:
        return ReweConfig.get_cookie_domain()

    def _on_load_error(self, browser_label: str, exc: Exception) -> None:
        super()._on_load_error(browser_label, exc)
        if _looks_like_locked_browser_profile(exc):
            message = "Browserprofil gesperrt"
            logger.info(
                "  Der %s laeuft vermutlich noch oder das Profil ist gesperrt. "
                "Bitte den Browser vollstaendig schliessen und den Import erneut starten.",
                browser_label,
            )
            raise ReweBrowserAuthError(message) from exc
        if "librewolf" in browser_label.lower() or "firefox" in browser_label.lower():
            logger.info(_SESSION_COOKIE_EXPLANATION)
            _log_rewe_firefox_session_diagnostics(browser_label)
            _session_cookie_hint(browser_label)

    def _on_no_cookies(self, browser_label: str) -> None:
        super()._on_no_cookies(browser_label)
        diagnostics = diagnose_session_cookies_for_domain(
            "firefox" if "firefox" in browser_label.lower() else "librewolf",
            ReweConfig.get_cookie_domain(),
        )
        if diagnostics.reason in {"recovery_missing", "recovery_unreadable", "recovery_empty"}:
            raise ReweBrowserAuthError("rstp nicht aus Browser-Session lesbar")
        logger.info(
            "Bitte melde dich zuerst bei www.rewe.de an oder nutze "
            "--cookies-file als Fallback."
        )
        if "librewolf" in browser_label.lower() or "firefox" in browser_label.lower():
            logger.info(_SESSION_COOKIE_EXPLANATION)
            _log_rewe_firefox_session_diagnostics(browser_label)
            _session_cookie_hint(browser_label)

    def _on_missing_required(
        self, cookie_names: Set[str], browser_label: str
    ) -> None:
        if KEYCLOAK_SSO_COOKIE_NAMES & cookie_names:
            logger.info(
                "Es wurden zwar REWE-/Keycloak-SSO-Cookies gefunden, aber kein rstp."
            )
            logger.info(_SESSION_COOKIE_EXPLANATION)
            _log_rewe_firefox_session_diagnostics(browser_label)
            _session_cookie_hint(browser_label)
            raise ReweBrowserAuthError(
                "rstp nicht aus Browser-Session lesbar"
            )
        else:
            logger.info(
                "Es wurde kein rstp-Cookie gefunden. Firefox/LibreWolf "
                "speichert Session-Cookies nur im Arbeitsspeicher."
            )
            if "librewolf" in browser_label.lower() or "firefox" in browser_label.lower():
                _log_rewe_firefox_session_diagnostics(browser_label)
                _session_cookie_hint(browser_label)
            raise ReweBrowserAuthError(
                "rstp fehlt im Browserprofil"
            )

        logger.info(
            "Alternativ: --cookies-file verwenden (Cookies per Browser-"
            "Erweiterung exportieren)."
        )

    def _on_missing_recommended(self, browser_label: str) -> None:
        logger.info(
            "⚠ Im lokalen %s-Profil wurden keine typischen "
            "WAF-/Cloudflare-Cookies gefunden.",
            browser_label,
        )

    def _validate_cookies(self, session, browser_label: str) -> bool:
        if not super()._validate_cookies(session, browser_label):
            return False

        expiry_epoch = extract_jwt_expiry_epoch(session.cookies, "rstp")
        if expiry_epoch is not None and is_jwt_expired(expiry_epoch):
            logger.error(
                "✗ Das REWE rstp-Cookie im lokalen %s-Profil ist abgelaufen. "
                "Bitte in REWE neu einloggen und erneut versuchen.",
                browser_label,
            )
            return False

        return True
