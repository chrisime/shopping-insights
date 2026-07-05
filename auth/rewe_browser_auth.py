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
from .session_cookie_recovery import check_sessionstore_privacy_level


_SESSION_COOKIE_EXPLANATION = (
    "Das rstp-Cookie ist ein reines Session-Cookie (ohne Ablaufdatum)\n"
    "und wird von Firefox/LibreWolf nur im Arbeitsspeicher gehalten,\n"
    "nicht in cookies.sqlite.\n"
    "Es kann nur aus der Session-Restore-Datei (recovery.jsonlz4)\n"
    "wiederhergestellt werden.\n"
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
        if "librewolf" in browser_label.lower() or "firefox" in browser_label.lower():
            logger.info(_SESSION_COOKIE_EXPLANATION)
            _session_cookie_hint(browser_label)

    def _on_no_cookies(self, browser_label: str) -> None:
        super()._on_no_cookies(browser_label)
        logger.info(
            "Bitte melde dich zuerst bei www.rewe.de an oder nutze "
            "--cookies-file als Fallback."
        )
        if "librewolf" in browser_label.lower() or "firefox" in browser_label.lower():
            logger.info(_SESSION_COOKIE_EXPLANATION)
            _session_cookie_hint(browser_label)

    def _on_missing_required(
        self, cookie_names: Set[str], browser_label: str
    ) -> None:
        if KEYCLOAK_SSO_COOKIE_NAMES & cookie_names:
            logger.info(
                "Es wurden zwar REWE-/Keycloak-SSO-Cookies gefunden, aber kein rstp."
            )
            logger.info(_SESSION_COOKIE_EXPLANATION)
            _session_cookie_hint(browser_label)
        else:
            logger.info(
                "Es wurde kein rstp-Cookie gefunden. Firefox/LibreWolf "
                "speichert Session-Cookies nur im Arbeitsspeicher."
            )
            if "librewolf" in browser_label.lower() or "firefox" in browser_label.lower():
                _session_cookie_hint(browser_label)

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
