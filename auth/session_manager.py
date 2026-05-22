"""Session management and API connection testing."""

from typing import Optional

from requests import Session

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


def setup_session(retailer: str, auth_method: Optional[str] = None, cookies_file: Optional[str] = None) -> Optional[Session]:
    """Setup an authenticated retailer session without testing the API connection."""
    normalized_retailer = retailer.lower()
    if auth_method is None:
        raise ValueError("auth_method must be provided to setup_session()")

    if normalized_retailer not in RETAILER_BROWSER_EXTRACTORS or normalized_retailer not in RETAILER_FILE_LOADERS:
        raise ValueError(f"Unbekannter Händler für Authentifizierung: {normalized_retailer}")

    if auth_method == "file":
        return RETAILER_FILE_LOADERS[normalized_retailer](cookies_file)

    return RETAILER_BROWSER_EXTRACTORS[normalized_retailer]().extract(auth_method)
