"""LIDL browser cookie extraction (subclass of BrowserCookieExtractor)."""

from typing import Set

from config import LidlConfig

from .browser_auth_base import BrowserCookieExtractor
from .cookie_policies import (
    LIDL_IDENTITY_COOKIE_NAMES as NAMED_LIDL_IDENTITY_COOKIE_NAMES,
    REQUIRED_LIDL_COOKIE_NAMES as NAMED_REQUIRED_LIDL_COOKIE_NAMES,
    RECOMMENDED_LIDL_COOKIE_NAMES as NAMED_RECOMMENDED_LIDL_COOKIE_NAMES,
)


REQUIRED_LIDL_COOKIE_NAMES = NAMED_REQUIRED_LIDL_COOKIE_NAMES
RECOMMENDED_LIDL_COOKIE_NAMES = NAMED_RECOMMENDED_LIDL_COOKIE_NAMES
LIDL_IDENTITY_COOKIE_NAMES = NAMED_LIDL_IDENTITY_COOKIE_NAMES


class LidlBrowserCookieExtractor(BrowserCookieExtractor):
    """Extract LIDL session cookies from a local browser profile."""

    retailer_name = "Lidl"
    # ``cookie_domain`` is country dependent and resolved at runtime.
    supported_browsers = LidlConfig.SUPPORTED_BROWSERS
    required_cookies = REQUIRED_LIDL_COOKIE_NAMES
    recommended_cookies = RECOMMENDED_LIDL_COOKIE_NAMES

    @property  # type: ignore[override]
    def cookie_domain(self) -> str:  # noqa: D401
        return LidlConfig.get_cookie_domain()

    def _on_load_error(self, browser_label: str, exc: Exception) -> None:
        print(f"✗ Fehler beim Extrahieren der {browser_label}-Cookies: {exc}")
        print("Bitte stelle sicher, dass:")
        print(f"1. {browser_label} läuft und du bei Lidl angemeldet bist")
        print(
            f"2. Die Lidl-Website (www.{self.cookie_domain}) in "
            f"{browser_label} geöffnet ist"
        )

    def _on_missing_required(
        self, cookie_names: Set[str], browser_label: str
    ) -> None:
        if LIDL_IDENTITY_COOKIE_NAMES & cookie_names:
            print(
                "Es wurden zwar typische Lidl-Konto-/Kontext-Cookies gefunden, "
                "aber kein authToken. Das deutet darauf hin, dass die Sitzung im "
                "Browser sichtbar ist, der eigentliche Auth-Cookie jedoch nicht "
                "im lokalen Profil verfügbar ist."
            )
        print(
            "Der Browser stellt offenbar nicht alle benoetigten Lidl-Session-Cookies "
            "lokal bereit. Nutze --cookies-file als Fallback oder teste einen "
            "anderen Browser."
        )

    def _on_missing_recommended(self, browser_label: str) -> None:
        print(
            f"⚠ Im lokalen {browser_label}-Profil wurden keine typischen "
            "Lidl-Zusatzcookies fuer eingeloggte Kontexte gefunden. Der Abruf kann "
            "dadurch spaeter an API- oder Kontextgrenzen scheitern."
        )

