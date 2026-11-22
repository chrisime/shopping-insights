"""Configuration constants for Rossmann digital-receipt integration.

Rossmann serves digital receipts through the white-label provider anybill.
This module centralizes the Rossmann account API (`rsmappapi.rossmann.net`)
endpoints and the anybill App API v4 endpoints/constants reverse-engineered
from the Rossmann Android app.
"""


class RossmannConfig:
    """Central Rossmann configuration for API access, auth and runtime behavior."""

    # File paths
    COOKIES_JSON_FILE = "rossmann_cookies.json"
    RECEIPTS_JSON_FILE = "rossmann_receipts.json"
    SKIPPED_RECEIPTS_REPORT_FILE = "rossmann_skipped_receipts.json"
    DEFAULT_OUTPUT_DIR = "tmp/rossmann"

    # Rossmann account API (rsmappapi.rossmann.net / account.ws)
    ACCOUNT_API_BASE_URL = "https://rsmappapi.rossmann.net/account.ws/v2"
    ACCOUNTS_LOGIN_ENDPOINT = "accounts/login"
    RECEIPT_DEV_ENDPOINT = "accounts/{account_id}/receipt/auth"
    ACCOUNT_HASH_HEADER = "Account-Hash"
    ACCOUNT_APP_VERSION = "5.11.1"
    ACCOUNT_BUILD_NUMBER = "421000110"
    ACCOUNT_PLATFORM = "android"
    ACCOUNT_PLATFORM_VERSION = "14"
    ACCOUNT_BUILD_SERIAL = "unknown"
    SSO_APP_URL = "https://www.rossmann.de/.rest/sso/app"
    X_API_KEY = "rqYCy0y0BH5+8ZU5"
    X_API_KEY_HEADER = "x-api-key"

    # anybill App API v4 (white-label receipt service)
    ANYBILL_API_BASE_URL = "https://app.anybill.de/"
    ANYBILL_API_VERSION = "api/v4/"
    ANYBILL_RECEIPT_ENDPOINT = "receipt"
    ANYBILL_RECEIPT_BY_ID_ENDPOINT = "receipt/{id}"
    ANYBILL_RECEIPT_PDF_ENDPOINT = "receipt/{id}/pdf"
    ANYBILL_RECEIPT_EXPORT_ENDPOINT = "receipt/export"
    ANYBILL_AUTH_REFRESH_ENDPOINT = "authentication/refresh"
    ANYBILL_CLIENT_ID = "4d8b1eb1-a1c6-45da-a271-5ab1167d6018"
    ANYBILL_TOKEN_PREFIX = "Bearer "

    # Request settings
    DEFAULT_TIMEOUT = 15
    REQUEST_DELAY = 0.3
    DEFAULT_PAGE_SIZE = 20
    MAX_RETRIES = 3
    RETRY_BACKOFF_SECONDS = 2
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    # Browser settings
    SUPPORTED_BROWSERS = {"firefox": "Firefox", "librewolf": "LibreWolf", "chrome": "Chrome", "chromium": "Chromium"}

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) "
        "Gecko/20100101 Firefox/148.0"
    )

    @classmethod
    def get_account_login_url(cls) -> str:
        """Return the Rossmann account login URL."""
        return f"{cls.ACCOUNT_API_BASE_URL}/{cls.ACCOUNTS_LOGIN_ENDPOINT}"

    @classmethod
    def get_receipt_auth_url(cls, account_id: str) -> str:
        """Return the Rossmann receipt-auth token URL for an account."""
        return (
            f"{cls.ACCOUNT_API_BASE_URL}/"
            f"{cls.RECEIPT_DEV_ENDPOINT.format(account_id=account_id)}"
        )

    @classmethod
    def get_anybill_url(cls, endpoint: str = "") -> str:
        """Return an absolute anybill App API v4 URL for the given endpoint path."""
        return f"{cls.ANYBILL_API_BASE_URL}{cls.ANYBILL_API_VERSION}{endpoint}"

    @classmethod
    def get_anybill_receipts_url(cls) -> str:
        """Return the anybill receipt list URL."""
        return cls.get_anybill_url(cls.ANYBILL_RECEIPT_ENDPOINT)

    @classmethod
    def get_anybill_receipt_detail_url(cls, receipt_id: str) -> str:
        """Return the anybill single-receipt URL."""
        return cls.get_anybill_url(
            cls.ANYBILL_RECEIPT_BY_ID_ENDPOINT.format(id=receipt_id)
        )

    @classmethod
    def get_anybill_receipt_pdf_url(cls, receipt_id: str) -> str:
        """Return the anybill receipt PDF URL."""
        return cls.get_anybill_url(
            cls.ANYBILL_RECEIPT_PDF_ENDPOINT.format(id=receipt_id)
        )

    @classmethod
    def get_anybill_refresh_url(cls) -> str:
        """Return the anybill token-refresh URL."""
        return cls.get_anybill_url(cls.ANYBILL_AUTH_REFRESH_ENDPOINT)

    @classmethod
    def get_country_code(cls) -> str:
        """Return the Rossmann country code in uppercase."""
        return "DE"

    @classmethod
    def get_cookie_domain(cls) -> str:
        """Return the primary cookie domain used by the Rossmann session."""
        return "rossmann.de"
