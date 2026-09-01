"""Configuration constants for dm purchase-history integration."""


class DmConfig:
    """Central dm configuration for API access, OAuth and runtime behavior."""

    # File paths
    COOKIES_JSON_FILE = "dm_cookies.json"
    RECEIPTS_JSON_FILE = "dm_receipts.json"
    SKIPPED_RECEIPTS_REPORT_FILE = "dm_skipped_receipts.json"
    DEFAULT_OUTPUT_DIR = "tmp/dm"

    # Backend APIs (reverse-engineered from account.dm.de/purchases)
    PURCHASE_HISTORY_URL = "https://purchasehistory-prod.services.dmtech.com"
    EBON_URL = "https://ebon-prod.services.dmtech.com"
    PURCHASE_HISTORY_ENDPOINT = "/v1/purchasehistory"
    EBONS_ENDPOINT = "/api/customer/ebons"

    # Products gateway (best-effort DAN enrichment)
    PRODUCTS_GATEWAY_URL = "https://products.dm.de"
    PRODUCTS_ENDPOINT = "/product"

    # OAuth 2.0 PKCE (signin.dm.de / dm-de/oauth-anonymous issuer)
    OAUTH_BASE_URL = "https://signin.dm.de"
    OAUTH_AUTHORIZE_PATH = "/dm-de/oauth-authorize"
    OAUTH_TOKEN_PATH = "/dm-de/oauth-token"
    OAUTH_CLIENT_ID = "nextaccount"
    OAUTH_REDIRECT_URI = "https://account.dm.de/callback"
    OAUTH_SCOPES = "openid email roles customerId"

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
    def get_purchase_history_url(cls) -> str:
        """Return the absolute purchase-history list URL."""
        return f"{cls.PURCHASE_HISTORY_URL}{cls.PURCHASE_HISTORY_ENDPOINT}"

    @classmethod
    def get_ebon_detail_url(cls, ebon_id: str) -> str:
        """Return the absolute eBon detail URL for one receipt."""
        return f"{cls.EBON_URL}{cls.EBONS_ENDPOINT}/{ebon_id}"

    @classmethod
    def get_ebon_download_url(cls, ebon_id: str) -> str:
        """Return the absolute eBon PDF download URL for one receipt."""
        return f"{cls.EBON_URL}{cls.EBONS_ENDPOINT}/{ebon_id}/download"

    @classmethod
    def get_product_url(cls, dan: str) -> str:
        """Return the best-effort product lookup URL for a DAN."""
        return f"{cls.PRODUCTS_GATEWAY_URL}{cls.PRODUCTS_ENDPOINT}/{dan}"

    @classmethod
    def get_authorize_url(cls) -> str:
        """Return the OAuth authorization endpoint URL."""
        return f"{cls.OAUTH_BASE_URL}{cls.OAUTH_AUTHORIZE_PATH}"

    @classmethod
    def get_token_url(cls) -> str:
        """Return the OAuth token endpoint URL."""
        return f"{cls.OAUTH_BASE_URL}{cls.OAUTH_TOKEN_PATH}"

    @classmethod
    def get_country_code(cls) -> str:
        """Return the dm country code in uppercase."""
        return "DE"

    @classmethod
    def get_cookie_domain(cls) -> str:
        """Return the primary cookie domain used by the dm session."""
        return "dm.de"