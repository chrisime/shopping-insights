"""LIDL browser cookie extraction (subclass of BrowserCookieExtractor)."""

import logging
from typing import Set

logger = logging.getLogger(__name__)
import requests

from config import LidlConfig

from .browser_auth_base import BrowserCookieExtractor
from .cookie_policies import (
    LIDL_IDENTITY_COOKIE_NAMES,
    REQUIRED_LIDL_COOKIE_NAMES,
    RECOMMENDED_LIDL_COOKIE_NAMES,
)
from .jwt_expiry import extract_jwt_expiry_epoch, is_jwt_expired


class LidlBrowserCookieExtractor(BrowserCookieExtractor):
    """Extract LIDL session cookies from a local browser profile."""

    retailer_name = "Lidl"
    supported_browsers = LidlConfig.SUPPORTED_BROWSERS
    required_cookies = REQUIRED_LIDL_COOKIE_NAMES
    recommended_cookies = RECOMMENDED_LIDL_COOKIE_NAMES

    @property  # type: ignore[override]
    def cookie_domain(self) -> str:
        return LidlConfig.get_cookie_domain()

    def _on_load_error(self, browser_label: str, exc: Exception) -> None:
        logger.error("✗ Fehler beim Extrahieren der %s-Cookies: %s", browser_label, exc)
        logger.info("Bitte stelle sicher, dass:")
        logger.info("1. %s läuft und du bei Lidl angemeldet bist", browser_label)
        logger.info("2. Die Lidl-Website (www.%s) in %s geöffnet ist", self.cookie_domain, browser_label)

    def _on_missing_required(
        self, cookie_names: Set[str], _browser_label: str
    ) -> None:
        if LIDL_IDENTITY_COOKIE_NAMES & cookie_names:
            logger.info(
                "Es wurden zwar typische Lidl-Konto-/Kontext-Cookies gefunden, "
                "aber kein authToken. Das deutet darauf hin, dass die Sitzung im "
                "Browser sichtbar ist, der eigentliche Auth-Cookie jedoch nicht "
                "im lokalen Profil verfügbar ist."
            )
        logger.info(
            "Der Browser stellt offenbar nicht alle benoetigten Lidl-Session-Cookies "
            "lokal bereit. Nutze --cookies-file als Fallback oder teste einen "
            "anderen Browser."
        )

    def _on_missing_recommended(self, browser_label: str) -> None:
        logger.info(
            "⚠ Im lokalen %s-Profil wurden keine typischen "
            "Lidl-Zusatzcookies fuer eingeloggte Kontexte gefunden.",
            browser_label,
        )

    def _validate_cookies(self, session: requests.Session, browser_label: str) -> bool:
        if not super()._validate_cookies(session, browser_label):
            return False

        expiry_epoch = extract_jwt_expiry_epoch(session.cookies, "authToken")
        if expiry_epoch is not None and is_jwt_expired(expiry_epoch):
            logger.error(
                "✗ Das LIDL authToken im lokalen %s-Profil ist abgelaufen. "
                "Bitte in Lidl neu einloggen und erneut versuchen.",
                browser_label,
            )
            return False

        return True

