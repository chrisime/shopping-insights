import unittest

from config.lidl_config import LidlConfig


class LidlConfigTests(unittest.TestCase):
    def setUp(self):
        LidlConfig.COUNTRY = "de"

    def tearDown(self):
        LidlConfig.COUNTRY = "de"

    def test_tickets_url_includes_country_de(self):
        self.assertIn("lidl.de", LidlConfig.get_tickets_url())

    def test_receipt_url_includes_receipt_id(self):
        url = LidlConfig.get_receipt_url("abc-123")
        self.assertIn("abc-123", url)

    def test_country_code_returns_uppercase(self):
        self.assertEqual(LidlConfig.get_country_code(), "DE")

    def test_language_code_returns_dash_format(self):
        self.assertEqual(LidlConfig.get_language_code(), "de-DE")

    def test_cookie_domain_returns_lidl_de(self):
        self.assertEqual(LidlConfig.get_cookie_domain(), "lidl.de")

    def test_set_country_updates_country(self):
        LidlConfig.set_country("bg")
        self.assertEqual(LidlConfig.COUNTRY, "bg")
        self.assertEqual(LidlConfig.get_country_code(), "BG")
        self.assertEqual(LidlConfig.get_language_code(), "bg-BG")
        self.assertEqual(LidlConfig.get_cookie_domain(), "lidl.bg")

    def test_set_country_is_case_insensitive(self):
        LidlConfig.set_country("NL")
        self.assertEqual(LidlConfig.COUNTRY, "nl")

    def test_constants_exist(self):
        self.assertTrue(hasattr(LidlConfig, "DEFAULT_TIMEOUT"))
        self.assertTrue(hasattr(LidlConfig, "MAX_RETRIES"))
        self.assertTrue(hasattr(LidlConfig, "RETRY_BACKOFF_SECONDS"))
        self.assertTrue(hasattr(LidlConfig, "RETRYABLE_STATUS_CODES"))


if __name__ == "__main__":
    unittest.main()
