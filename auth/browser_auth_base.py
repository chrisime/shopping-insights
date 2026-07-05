"""Shared base class for browser-based cookie extraction.

Both LIDL and REWE need to read authentication cookies from a locally
installed browser profile and turn them into a :class:`requests.Session`.
The high-level algorithm is identical, only filtering, validation and
user-facing wording differ. This module captures the shared algorithm in
:class:`BrowserCookieExtractor`; retailer-specific subclasses override a few
hooks.
"""

from __future__ import annotations

import logging

from typing import Callable, Dict, Iterable, Mapping, Optional, Set

logger = logging.getLogger(__name__)

import browser_cookie3
import requests
from requests.cookies import create_cookie

from .session_cookie_recovery import read_session_cookies_for_domain
from .shared_file_auth import analyze_cookie_names


# Single source of truth for the available browser_cookie3 loaders.
# Subclasses pick a subset via ``supported_browsers``.
ALL_BROWSER_LOADERS: Dict[str, Callable] = {
    "firefox": browser_cookie3.firefox,
    "librewolf": browser_cookie3.librewolf,
    "chrome": browser_cookie3.chrome,
    "chromium": browser_cookie3.chromium,
}


class BrowserCookieExtractor:
    """Template-method base class for browser cookie extraction.

    Subclasses must override :attr:`retailer_name`, :attr:`cookie_domain`
    and :attr:`supported_browsers`. They may override the various ``_*``
    hooks to add retailer-specific behavior (User-Agent, domain filter,
    required cookie validation, error messages, ...).
    """

    # --- Required configuration (subclasses override) ---------------------
    retailer_name: str = ""
    cookie_domain: str = ""
    # Mapping browser key -> display name (e.g. {"firefox": "Firefox"})
    supported_browsers: Mapping[str, str] = {}

    # --- Optional configuration -------------------------------------------
    default_user_agent: Optional[str] = None
    # Cookies that MUST be present after extraction; emptiness disables check.
    required_cookies: Set[str] = set()
    # Cookies whose absence triggers a soft warning.
    recommended_cookies: Set[str] = set()
    # Whether the cookie's ``expires`` value should be carried over.
    include_expires: bool = False
    # Whether to drop cookies whose domain does not end in ``cookie_domain``.
    filter_by_domain_suffix: bool = False

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def extract(self, browser: str = "firefox") -> Optional[requests.Session]:
        """Extract cookies from the given browser into a ``requests.Session``.

        Returns ``None`` on any error so callers can fall back gracefully.
        """
        loader = ALL_BROWSER_LOADERS.get(browser)
        if browser not in self.supported_browsers or loader is None:
            logger.error("✗ Unbekannter Browser für %s: %s", self.retailer_name, browser)
            logger.info("Unterstützt werden: %s", ", ".join(self.supported_browsers.keys()))
            return None

        browser_label = self.supported_browsers.get(browser, browser)
        logger.info("ℹ Extrahiere %s-Cookies für %s aus %s-Profil...", self.retailer_name, self.cookie_domain, browser_label)

        try:
            cookies = loader(domain_name=self.cookie_domain)
        except Exception as exc:  # pragma: no cover - environment dependent
            self._on_load_error(browser_label, exc)
            return None

        session = self._build_session()
        cookie_count = self._populate_session(session, cookies)

        # Firefox/LibreWolf store session-only cookies (no expiry) only in
        # memory. Try to recover them from the session-restore file so that
        # cookies like REWE's ``rstp`` are available.
        if browser in ("firefox", "librewolf"):
            cookie_count += self._merge_session_cookies(session, browser)

        if cookie_count == 0:
            self._on_no_cookies(browser_label)
            return None

        if not self._validate_cookies(session, browser_label):
            return None

        logger.info("✓ Erfolgreich %d %s-Cookies aus %s extrahiert", cookie_count, self.retailer_name, browser_label)
        return session

    # ----------------------------------------------------------------------
    # Hooks (subclasses may override)
    # ----------------------------------------------------------------------
    def _build_session(self) -> requests.Session:
        session = requests.Session()
        if self.default_user_agent:
            session.headers.update({"User-Agent": self.default_user_agent})
        return session

    def _populate_session(
        self, session: requests.Session, cookies: Iterable
    ) -> int:
        count = 0
        for cookie in cookies:
            if self.filter_by_domain_suffix:
                normalized = cookie.domain.lower().lstrip(".")
                if not normalized.endswith(self.cookie_domain):
                    continue

            kwargs = {
                "domain": cookie.domain,
                "name": cookie.name,
                "value": cookie.value,
                "secure": cookie.secure,
                "path": cookie.path,
            }
            if self.include_expires:
                kwargs["expires"] = cookie.expires

            session.cookies.set_cookie(create_cookie(**kwargs))
            count += 1
        return count

    def _merge_session_cookies(
        self, session: requests.Session, browser: str
    ) -> int:
        """Merge session-only cookies from the session-restore file.

        Only adds cookies whose name is not already present in the session
        so that persistent cookies from ``cookies.sqlite`` take precedence.
        """
        existing_names = {cookie.name for cookie in session.cookies}

        session_cookies = read_session_cookies_for_domain(
            browser, self.cookie_domain,
        )
        added = 0
        for cookie_data in session_cookies:
            name = cookie_data.get("name", "")
            if not name or name in existing_names:
                continue
            session.cookies.set_cookie(
                create_cookie(
                    domain=cookie_data.get("domain", ""),
                    name=name,
                    value=cookie_data.get("value", ""),
                    path=cookie_data.get("path", "/"),
                    secure=bool(cookie_data.get("secure", False)),
                )
            )
            existing_names.add(name)
            added += 1
        if added:
            logger.info("  + %d Session-Cookie(s) aus %s-Session-Restore ergänzt", added, browser.title())
        return added

    def _validate_cookies(
        self, session: requests.Session, browser_label: str
    ) -> bool:
        """Default validation: enforce required + warn on missing recommended."""
        analysis = analyze_cookie_names(
            (cookie.name for cookie in session.cookies),
            required_cookies=self.required_cookies,
            recommended_cookies=self.recommended_cookies,
        )

        if analysis.missing_required:
            logger.error("✗ Im lokalen %s-Profil fehlen wichtige %s-Session-Cookies: %s", browser_label, self.retailer_name, ", ".join(analysis.missing_required))
            self._on_missing_required(set(analysis.cookie_names), browser_label)
            return False

        if self.recommended_cookies and not (
            set(analysis.cookie_names) & self.recommended_cookies
        ):
            self._on_missing_recommended(browser_label)

        return True

    # ----- Logging hooks --------------------------------------------------
    def _on_load_error(self, browser_label: str, exc: Exception) -> None:
        logger.error("✗ Fehler beim Lesen der %s-Cookies aus %s: %s", self.retailer_name, browser_label, exc)
        logger.info("Bitte stelle sicher, dass:")
        logger.info("1. %s lokal installiert ist", browser_label)
        logger.info("2. du in %s bei %s angemeldet bist", browser_label, self.retailer_name)
        logger.info("3. der Browserzugriff auf das lokale Profil bzw. die Keychain erlaubt ist")

    def _on_no_cookies(self, browser_label: str) -> None:
        logger.error("✗ Keine %s-Cookies im lokalen %s-Profil gefunden.", self.retailer_name, browser_label)

    def _on_missing_required(
        self, cookie_names: Set[str], browser_label: str
    ) -> None:
        """Hook for retailer-specific extra hints when required cookies are missing."""
        return None

    def _on_missing_recommended(self, browser_label: str) -> None:
        logger.info("⚠ Im lokalen %s-Profil wurden keine empfohlenen %s-Zusatzcookies gefunden.", browser_label, self.retailer_name)

