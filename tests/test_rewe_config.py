import unittest

from config.rewe_config import ReweConfig


class ReweConfigTests(unittest.TestCase):
    def test_receipts_zip_url_contains_base(self):
        self.assertIn("rewe.de", ReweConfig.get_receipts_zip_url())
        self.assertIn("/api/receipts/zip", ReweConfig.get_receipts_zip_url())

    def test_coupon_wallet_url_contains_base(self):
        self.assertIn("rewe.de", ReweConfig.get_coupon_wallet_url())

    def test_mydata_receipts_url_contains_base(self):
        self.assertIn("rewe.de", ReweConfig.get_mydata_receipts_url())

    def test_cookie_domain_is_rewe_de(self):
        self.assertEqual(ReweConfig.get_cookie_domain(), "rewe.de")

    def test_country_code_returns_uppercase(self):
        self.assertEqual(ReweConfig.get_country_code(), "DE")

    def test_constants_exist(self):
        self.assertTrue(hasattr(ReweConfig, "DEFAULT_TIMEOUT"))
        self.assertTrue(hasattr(ReweConfig, "MAX_RETRIES"))
        self.assertTrue(hasattr(ReweConfig, "RETRY_BACKOFF_SECONDS"))
        self.assertTrue(hasattr(ReweConfig, "SUPPORTED_BROWSERS"))


if __name__ == "__main__":
    unittest.main()
