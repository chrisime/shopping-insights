"""REWE browser cookie extraction (subclass of BrowserCookieExtractor)."""

from typing import Set

from config import ReweConfig

from .browser_auth_base import BrowserCookieExtractor
from .cookie_policies import (
    KEYCLOAK_SSO_COOKIE_NAMES,
    REQUIRED_REWE_COOKIE_NAMES,
    RECOMMENDED_REWE_WAF_COOKIE_NAMES,
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

    def _on_no_cookies(self, browser_label: str) -> None:
        super()._on_no_cookies(browser_label)
        print(
            "Bitte melde dich zuerst bei www.rewe.de an oder nutze "
            "--cookies-file als Fallback."
        )

    def _on_missing_required(
        self, cookie_names: Set[str], browser_label: str
    ) -> None:
        if KEYCLOAK_SSO_COOKIE_NAMES & cookie_names:
            print(
                "Es wurden zwar REWE-/Keycloak-SSO-Cookies gefunden, aber kein "
                "rstp. Das rstp-Cookie ist ein reiner Session-Cookie (ohne "
                "Ablaufdatum) und wird von Firefox/LibreWolf nur im "
                "Arbeitsspeicher gehalten – nicht in cookies.sqlite."
            )
            if "librewolf" in browser_label.lower():
                print(
                    "  LibreWolf verhindert standardmaessig, dass Session-Cookies "
                    "in der Session-Restore-Datei (recovery.jsonlz4) gespeichert "
                    "werden (browser.sessionstore.privacy_level = 2)."
                )
                print(
                    "  Fix: In about:config den Wert "
                    "browser.sessionstore.privacy_level auf 0 setzen, "
                    "LibreWolf neu starten und erneut bei REWE anmelden."
                )
                print(
                    "  Details: docs/LIBREWOLF_SESSION_COOKIES.md"
                )
            else:
                print(
                    "  Hinweis: Falls der Browser laeuft und eine aktive "
                    "REWE-Session hat, sollte rstp aus der Session-Restore-Datei "
                    "(recovery.jsonlz4) gelesen werden koennen."
                )
        print(
            "Alternativ: --cookies-file verwenden (Cookies per Browser-"
            "Erweiterung exportieren)."
        )

    def _on_missing_recommended(self, browser_label: str) -> None:
        print(
            f"⚠ Im lokalen {browser_label}-Profil wurden keine typischen "
            "WAF-/Cloudflare-Cookies gefunden. Der REWE-Abruf kann dadurch "
            "mit 403 scheitern."
        )

