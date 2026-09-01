"""dm browser cookie extraction (subclass of BrowserCookieExtractor)."""

import logging

logger = logging.getLogger(__name__)

import requests

from config import DmConfig

from .browser_auth_base import BrowserCookieExtractor
from .cookie_policies import (
    DM_RECOMMENDED_COOKIE_PREFIXES,
    DM_REQUIRED_COOKIE_NAMES,
    DM_REQUIRED_COOKIE_PREFIXES,
)


def _dm_has_session_cookie(cookie_names: set[str]) -> bool:
    return bool(DM_REQUIRED_COOKIE_NAMES & cookie_names) or any(
        name.startswith(DM_REQUIRED_COOKIE_PREFIXES) for name in cookie_names
    )


def _dm_has_recommended_cookie(cookie_names: set[str]) -> bool:
    return any(
        name.startswith(DM_RECOMMENDED_COOKIE_PREFIXES) for name in cookie_names
    )


class DmBrowserCookieExtractor(BrowserCookieExtractor):
    """Extract dm session cookies from a local browser profile.

    The dm cookie domain is ``dm.de``, which also covers the host-only
    ``signin.dm.de`` session cookies needed for the OAuth flow.
    """

    retailer_name = "dm"
    supported_browsers = DmConfig.SUPPORTED_BROWSERS
    default_user_agent = DmConfig.DEFAULT_USER_AGENT
    cookie_domain = "dm.de"
    include_expires = True
    filter_by_domain_suffix = True

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self.default_user_agent:
            session.headers.update({"User-Agent": self.default_user_agent})
        return session

    def _validate_cookies(self, session, browser_label: str) -> bool:
        cookie_names = {cookie.name for cookie in session.cookies}
        if not _dm_has_session_cookie(cookie_names):
            logger.error(
                "✗ Im lokalen %s-Profil fehlen dm-Session-Cookies. "
                "Bitte melde dich bei account.dm.de an und versuche es erneut.",
                browser_label,
            )
            return False
        if not _dm_has_recommended_cookie(cookie_names):
            logger.info(
                "ℹ Es wurden keine hilfreichen dm-Zusatzcookies gefunden, "
                "die Session-Cookies sind aber vorhanden."
            )
        return True