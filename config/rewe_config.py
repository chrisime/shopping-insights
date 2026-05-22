"""Configuration values for REWE eBon download."""


class ReweConfig:
    """Central REWE configuration for API access and runtime behavior."""

    COUNTRY = "de"

    BASE_URL = "https://www.rewe.de"
    RECEIPTS_ZIP_ENDPOINT = "/api/receipts/zip"
    COUPON_WALLET_ENDPOINT = "/shop/mydata/couponwallet"
    MYDATA_RECEIPTS_PATH = "/shop/mydata/meine-einkaeufe/im-markt"

    SUPPORTED_BROWSERS = {"firefox": "Firefox", "librewolf": "LibreWolf", "chrome": "Chrome", "chromium": "Chromium"}

    DEFAULT_TIMEOUT = 30
    INTERACTIVE_LOGIN_TIMEOUT = 300
    MAX_RETRIES = 3
    RETRY_BACKOFF_SECONDS = 2

    REWE_COOKIES_JSON_FILE = "rewe_cookies.json"
    RECEIPTS_JSON_FILE = "rewe_receipts.json"
    SKIPPED_RECEIPTS_REPORT_FILE = "rewe_skipped_receipts.json"
    REWE_DEFAULT_OUTPUT_DIR = "tmp/rewe"

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) "
        "Gecko/20100101 Firefox/148.0"
    )

    @classmethod
    def get_receipts_zip_url(cls) -> str:
        """Return absolute URL for the ZIP receipts endpoint."""
        return f"{cls.BASE_URL}{cls.RECEIPTS_ZIP_ENDPOINT}"

    @classmethod
    def get_coupon_wallet_url(cls) -> str:
        """Return absolute URL for the coupon wallet endpoint."""
        return f"{cls.BASE_URL}{cls.COUPON_WALLET_ENDPOINT}"

    @classmethod
    def get_mydata_receipts_url(cls) -> str:
        """Return absolute URL for the REWE in-store receipts page."""
        return f"{cls.BASE_URL}{cls.MYDATA_RECEIPTS_PATH}"

    @classmethod
    def get_cookie_domain(cls) -> str:
        """Get the domain for cookie extraction"""
        return "rewe.de"

    @classmethod
    def get_country_code(cls) -> str:
        """Return the configured REWE country code in uppercase."""
        return cls.COUNTRY.upper()

