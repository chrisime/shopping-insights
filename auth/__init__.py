"""Authentication module for shopping analyzer."""

from .lidl_file_auth import diagnose_lidl_cookie_file, load_lidl_cookies_from_file
from .lidl_browser_auth import LidlBrowserCookieExtractor
from .rewe_browser_auth import ReweBrowserCookieExtractor
from .rewe_customer_id import cache_customer_id, resolve_rewe_customer_id
from .rewe_file_auth import diagnose_rewe_cookie_file, load_rewe_cookies_from_file
from .session_manager import setup_session

__all__ = [
    "cache_customer_id",
    "diagnose_lidl_cookie_file",
    "LidlBrowserCookieExtractor",
    "ReweBrowserCookieExtractor",
    "load_lidl_cookies_from_file",
    "diagnose_rewe_cookie_file",
    "load_rewe_cookies_from_file",
    "resolve_rewe_customer_id",
    "setup_session",
]
