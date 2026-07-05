import unittest

from shared.addresses import empty_address, normalize_address


class AddressesTests(unittest.TestCase):
    # --- empty_address ---
    def test_empty_address_returns_all_none(self):
        result = empty_address()
        self.assertEqual(
            result, {"street": None, "street_no": None, "zip": None, "city": None}
        )

    # --- normalize_address ---
    def test_normalize_address_returns_empty_for_non_dict(self):
        self.assertEqual(normalize_address(None), empty_address())
        self.assertEqual(normalize_address("str"), empty_address())
        self.assertEqual(normalize_address([]), empty_address())

    def test_normalize_address_strips_string_values(self):
        result = normalize_address(
            {"street": "  Hauptstr.  ", "city": "Berlin  ", "zip": "10115"}
        )
        self.assertEqual(result["street"], "Hauptstr.")
        self.assertEqual(result["city"], "Berlin")
        self.assertEqual(result["zip"], 10115)

    def test_normalize_address_skips_none_fields(self):
        result = normalize_address({"street": "Teststr. 1", "zip": None})
        self.assertEqual(result["street"], "Teststr. 1")
        self.assertIsNone(result["street_no"])
        self.assertIsNone(result["zip"])
        self.assertIsNone(result["city"])

    def test_normalize_address_converts_empty_strings_to_none(self):
        result = normalize_address({"street": "  ", "city": ""})
        self.assertIsNone(result["street"])
        self.assertIsNone(result["city"])

    def test_normalize_address_handles_integer_zip(self):
        result = normalize_address({"zip": 80331})
        self.assertEqual(result["zip"], 80331)

    def test_normalize_address_rejects_invalid_zip(self):
        result = normalize_address({"zip": "00000"})
        self.assertIsNone(result["zip"])

    def test_normalize_address_rejects_too_low_zip(self):
        result = normalize_address({"zip": 1000})
        self.assertIsNone(result["zip"])

    def test_normalize_address_rejects_too_high_zip(self):
        result = normalize_address({"zip": 99999})
        self.assertIsNone(result["zip"])

    def test_normalize_address_accepts_boundary_zips(self):
        self.assertEqual(normalize_address({"zip": "01067"})["zip"], 1067)
        self.assertEqual(normalize_address({"zip": 99998})["zip"], 99998)


if __name__ == "__main__":
    unittest.main()
