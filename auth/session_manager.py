"""Session management and API connection testing."""

from typing import Optional

import requests

from .lidl_file_auth import load_lidl_cookies_from_file
from .lidl_browser_auth import LidlBrowserCookieExtractor
from .rewe_browser_auth import ReweBrowserCookieExtractor
from .rewe_file_auth import load_rewe_cookies_from_file

RETAILER_BROWSER_EXTRACTORS = {
    "lidl": LidlBrowserCookieExtractor,
    "rewe": ReweBrowserCookieExtractor,
}

RETAILER_FILE_LOADERS = {
    "lidl": load_lidl_cookies_from_file,
    "rewe": load_rewe_cookies_from_file,
}


def setup_session(
    retailer: str = "lidl",
    auth_method: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> Optional[requests.Session]:
    """Setup an authenticated retailer session without testing the API connection."""
    normalized_retailer = retailer.lower()
    if auth_method is None:
        raise ValueError("auth_method must be provided to setup_session()")

    return _load_session_for_retailer(
        retailer=normalized_retailer,
        auth_method=auth_method,
        cookies_file=cookies_file,
    )


def _load_session_for_retailer(
    retailer: str,
    auth_method: str,
    cookies_file: Optional[str],
) -> Optional[requests.Session]:
    if retailer not in RETAILER_BROWSER_EXTRACTORS or retailer not in RETAILER_FILE_LOADERS:
        raise ValueError(f"Unbekannter Händler für Authentifizierung: {retailer}")


    if auth_method == "file":
        return RETAILER_FILE_LOADERS[retailer](cookies_file)

    extractor_cls = RETAILER_BROWSER_EXTRACTORS[retailer]
    return extractor_cls().extract(auth_method)


