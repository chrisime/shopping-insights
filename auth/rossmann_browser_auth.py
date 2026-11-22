"""Rossmann browser cookie extraction (subclass of BrowserCookieExtractor)."""

import logging

logger = logging.getLogger(__name__)

import requests

from config import RossmannConfig

from .browser_auth_base import BrowserCookieExtractor
from .cookie_policies import ROSSMANN_SESSION_COOKIE_PREFIXES


def _rossmann_has_session_cookie(cookie_names: set[str]) -> bool:
    return any(
        name.startswith(ROSSMANN_SESSION_COOKIE_PREFIXES) for name in cookie_names
    )


class RossmannBrowserCookieExtractor(BrowserCookieExtractor):
    """Extract Rossmann session cookies from a local browser profile.

    Uses the shared ``rossmann`` domain suffix so cookies from both
    ``*.rossmann.de`` and ``*.rossmann.net`` are included; the actual session
    validity is confirmed at runtime via the anybill token mint.
    """

    retailer_name = "rossmann"
    supported_browsers = RossmannConfig.SUPPORTED_BROWSERS
    default_user_agent = RossmannConfig.DEFAULT_USER_AGENT
    cookie_domain = "rossmann"
    include_expires = True
    filter_by_domain_suffix = True

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self.default_user_agent:
            session.headers.update({"User-Agent": self.default_user_agent})
        return session

    def _validate_cookies(self, session, browser_label: str) -> bool:
        cookie_names = {cookie.name for cookie in session.cookies}
        if not cookie_names:
            logger.error(
                "✗ Im lokalen %s-Profil wurden keine Rossmann-Cookies gefunden. "
                "Bitte melde dich bei der Rossmann-App bzw. www.rossmann.de an "
                "und versuche es erneut.",
                browser_label,
            )
            return False
        if not _rossmann_has_session_cookie(cookie_names):
            logger.info(
                "ℹ Es wurden Rossmann-Cookies gefunden, aber keine offensichtliche "
                "Session. Die Gültigkeit wird beim Token-Mint geprüft."
            )
        return True