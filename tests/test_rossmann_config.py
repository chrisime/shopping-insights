import unittest

from config.rossmann_config import RossmannConfig
from shared.retailer_runtime import RETAILERS, get_retailer_runtime


class RossmannConfigTests(unittest.TestCase):
    def test_anybill_receipts_url(self):
        url = RossmannConfig.get_anybill_receipts_url()
        self.assertIn("app.anybill.de", url)
        self.assertIn("/api/v4/receipt", url)

    def test_anybill_detail_url_includes_id(self):
        url = RossmannConfig.get_anybill_receipt_detail_url("abc-123")
        self.assertIn("/receipt/abc-123", url)

    def test_anybill_pdf_url_includes_pdf(self):
        url = RossmannConfig.get_anybill_receipt_pdf_url("abc-123")
        self.assertIn("/receipt/abc-123/pdf", url)

    def test_anybill_client_id(self):
        self.assertEqual(
            RossmannConfig.ANYBILL_CLIENT_ID,
            "4d8b1eb1-a1c6-45da-a271-5ab1167d6018",
        )

    def test_account_login_url(self):
        self.assertIn("rsmappapi.rossmann.net", RossmannConfig.get_account_login_url())
        self.assertIn("/accounts/login", RossmannConfig.get_account_login_url())

    def test_receipt_auth_url_includes_account_id(self):
        url = RossmannConfig.get_receipt_auth_url("acct-1")
        self.assertIn("acct-1", url)
        self.assertIn("/receipt/auth", url)

    def test_anybill_refresh_url(self):
        self.assertIn("/authentication/refresh", RossmannConfig.get_anybill_refresh_url())

    def test_cookie_domain(self):
        self.assertEqual(RossmannConfig.get_cookie_domain(), "rossmann.de")

    def test_constants_exist(self):
        self.assertTrue(hasattr(RossmannConfig, "DEFAULT_TIMEOUT"))
        self.assertTrue(hasattr(RossmannConfig, "MAX_RETRIES"))
        self.assertTrue(hasattr(RossmannConfig, "RETRYABLE_STATUS_CODES"))


class RossmannRetailerRuntimeTests(unittest.TestCase):
    def test_rossmann_is_registered(self):
        self.assertIn("rossmann", RETAILERS)

    def test_get_retailer_runtime_returns_rossmann(self):
        runtime = get_retailer_runtime("rossmann")
        if runtime is None:
            self.fail("rossmann runtime missing")
        self.assertEqual(runtime.code, "rossmann")
        self.assertEqual(runtime.name, "ROSSMANN")
        self.assertEqual(runtime.country, "DE")
        self.assertEqual(runtime.receipts_json_file, "rossmann_receipts.json")


if __name__ == "__main__":
    unittest.main()