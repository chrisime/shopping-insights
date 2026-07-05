import unittest

from shared.retailer_runtime import RETAILERS, RetailerRuntime, get_retailer_runtime


class RetailerRuntimeTests(unittest.TestCase):
    # --- RETAILERS ---
    def test_retailers_contains_lidl_and_rewe(self):
        self.assertIn("lidl", RETAILERS)
        self.assertIn("rewe", RETAILERS)

    # --- get_retailer_runtime ---
    def test_get_retailer_runtime_returns_lidl(self):
        runtime = get_retailer_runtime("lidl")
        self.assertIsInstance(runtime, RetailerRuntime)
        self.assertEqual(runtime.code, "lidl")
        self.assertEqual(runtime.name, "LIDL")

    def test_get_retailer_runtime_returns_rewe(self):
        runtime = get_retailer_runtime("rewe")
        self.assertIsInstance(runtime, RetailerRuntime)
        self.assertEqual(runtime.code, "rewe")
        self.assertEqual(runtime.name, "REWE")

    def test_get_retailer_runtime_is_case_insensitive(self):
        lidl = get_retailer_runtime("LIDL")
        rewe = get_retailer_runtime("Rewe")
        self.assertEqual(lidl.code, "lidl")
        self.assertEqual(rewe.code, "rewe")

    def test_get_retailer_runtime_strips_whitespace(self):
        runtime = get_retailer_runtime("  lidl  ")
        self.assertEqual(runtime.code, "lidl")

    def test_get_retailer_runtime_returns_none_for_unknown(self):
        self.assertIsNone(get_retailer_runtime("edeka"))
        self.assertIsNone(get_retailer_runtime(""))

    def test_get_retailer_runtime_returns_none_for_empty_after_strip(self):
        self.assertIsNone(get_retailer_runtime("   "))

    def test_get_retailer_runtime_includes_country_from_config(self):
        runtime = get_retailer_runtime("lidl")
        self.assertEqual(runtime.country, "DE")

    def test_get_retailer_runtime_uses_default_json_files(self):
        lidl = get_retailer_runtime("lidl")
        rewe = get_retailer_runtime("rewe")
        self.assertEqual(lidl.receipts_json_file, "lidl_receipts.json")
        self.assertEqual(rewe.receipts_json_file, "rewe_receipts.json")

    # --- RetailerRuntime dataclass ---
    def test_retailer_runtime_frozen(self):
        runtime = RetailerRuntime("lidl", "LIDL", "DE", "lidl_receipts.json")
        with self.assertRaises(AttributeError):
            runtime.code = "rewe"


if __name__ == "__main__":
    unittest.main()
