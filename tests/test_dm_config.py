import unittest

from config.dm_config import DmConfig
from shared.retailer_runtime import RETAILERS, get_retailer_runtime


class DmConfigTests(unittest.TestCase):
    def test_purchase_history_url(self):
        url = DmConfig.get_purchase_history_url()
        self.assertIn("purchasehistory-prod.services.dmtech.com", url)
        self.assertIn("/v1/purchasehistory", url)

    def test_ebon_detail_url_includes_id(self):
        url = DmConfig.get_ebon_detail_url("abc-123_2026")
        self.assertIn("abc-123_2026", url)
        self.assertIn("/api/customer/ebons/", url)

    def test_ebon_download_url_includes_download(self):
        url = DmConfig.get_ebon_download_url("abc-123_2026")
        self.assertIn("/api/customer/ebons/abc-123_2026/download", url)

    def test_product_url_includes_dan(self):
        url = DmConfig.get_product_url("1446511")
        self.assertIn("products.dm.de", url)
        self.assertIn("/product/1446511", url)

    def test_authorize_url(self):
        self.assertIn("signin.dm.de", DmConfig.get_authorize_url())
        self.assertIn("/dm-de/oauth-authorize", DmConfig.get_authorize_url())

    def test_token_url(self):
        self.assertIn("signin.dm.de", DmConfig.get_token_url())
        self.assertIn("/dm-de/oauth-token", DmConfig.get_token_url())

    def test_country_code_returns_de(self):
        self.assertEqual(DmConfig.get_country_code(), "DE")

    def test_cookie_domain(self):
        self.assertEqual(DmConfig.get_cookie_domain(), "dm.de")

    def test_constants_exist(self):
        self.assertTrue(hasattr(DmConfig, "DEFAULT_TIMEOUT"))
        self.assertTrue(hasattr(DmConfig, "MAX_RETRIES"))
        self.assertTrue(hasattr(DmConfig, "RETRY_BACKOFF_SECONDS"))
        self.assertTrue(hasattr(DmConfig, "RETRYABLE_STATUS_CODES"))
        self.assertEqual(DmConfig.OAUTH_CLIENT_ID, "nextaccount")
        self.assertIn("openid", DmConfig.OAUTH_SCOPES)


class DmRetailerRuntimeTests(unittest.TestCase):
    def test_dm_is_registered(self):
        self.assertIn("dm", RETAILERS)

    def test_get_retailer_runtime_returns_dm(self):
        runtime = get_retailer_runtime("dm")
        if runtime is None:
            self.fail("dm runtime missing")
        self.assertEqual(runtime.code, "dm")
        self.assertEqual(runtime.name, "DM")
        self.assertEqual(runtime.country, "DE")
        self.assertEqual(runtime.receipts_json_file, "dm_receipts.json")


if __name__ == "__main__":
    unittest.main()