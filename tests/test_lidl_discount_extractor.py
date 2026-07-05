import unittest
from bs4 import BeautifulSoup

from parsing.lidl_discount_extractor import apply_lidl_discount_fields, apply_lidl_plus_discount


class LidlDiscountExtractorTests(unittest.TestCase):
    # --- apply_lidl_discount_fields ---
    def test_apply_lidl_discount_fields_extracts_preisvorteil(self):
        soup = BeautifulSoup(
            '<span class="purchase_list">Preisvorteil -1,50\nanderes Zeug</span>',
            "html.parser",
        )
        result = apply_lidl_discount_fields({}, soup)
        self.assertEqual(result.get("discount"), 1.5)

    def test_apply_lidl_discount_fields_extracts_rabatt_as_sticker(self):
        soup = BeautifulSoup(
            '<span class="purchase_list">Rabatt 20% -0,80\n</span>',
            "html.parser",
        )
        result = apply_lidl_discount_fields({}, soup)
        self.assertEqual(result.get("sticker_discount"), 0.8)
        self.assertEqual(result.get("sticker_discount_pct"), [20])

    def test_apply_lidl_discount_fields_skips_lidl_plus_rabatt(self):
        soup = BeautifulSoup(
            '<span class="purchase_list">Lidl Plus Rabatt -0,50\n</span>',
            "html.parser",
        )
        result = apply_lidl_discount_fields({}, soup)
        self.assertIsNone(result.get("discount"))
        self.assertIsNone(result.get("sticker_discount"))

    def test_apply_lidl_discount_fields_returns_original_when_no_purchase_list(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        result = apply_lidl_discount_fields({"existing": True}, soup)
        self.assertEqual(result, {"existing": True})

    def test_apply_lidl_discount_fields_tolerates_malformed_html(self):
        soup = BeautifulSoup(
            '<span class="purchase_list">irgendwas</span>', "html.parser"
        )
        result = apply_lidl_discount_fields({}, soup)
        self.assertEqual(result, {})

    def test_apply_lidl_discount_fields_skips_gesamter_preisvorteil(self):
        soup = BeautifulSoup(
            '<span class="purchase_list">Gesamter Preisvorteil -5,00</span>',
            "html.parser",
        )
        result = apply_lidl_discount_fields({}, soup)
        self.assertIsNone(result.get("discount"))

    def test_apply_lidl_discount_fields_skips_gesamter_rabatt(self):
        soup = BeautifulSoup(
            '<span class="purchase_list">Gesamter Rabatt -3,00</span>',
            "html.parser",
        )
        result = apply_lidl_discount_fields({}, soup)
        self.assertIsNone(result.get("discount"))

    # --- apply_lidl_plus_discount ---
    def test_apply_lidl_plus_discount_extracts_from_vat_info(self):
        soup = BeautifulSoup(
            '<span class="vat_info">1,50 EUR gespart</span>',
            "html.parser",
        )
        result = apply_lidl_plus_discount({}, soup)
        self.assertEqual(result.get("lidlplus_discount"), 1.5)

    def test_apply_lidl_plus_discount_falls_back_to_page_text(self):
        soup = BeautifulSoup(
            '<html><body>irgendwas 2,00 EUR gespart hier</body></html>',
            "html.parser",
        )
        result = apply_lidl_plus_discount({}, soup)
        self.assertEqual(result.get("lidlplus_discount"), 2.0)

    def test_apply_lidl_plus_discount_sets_none_when_no_discount(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        result = apply_lidl_plus_discount({}, soup)
        self.assertIsNone(result.get("lidlplus_discount"))

    def test_apply_lidl_plus_discount_preserves_existing_value(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        result = apply_lidl_plus_discount({"lidlplus_discount": 0.5}, soup)
        self.assertEqual(result.get("lidlplus_discount"), 0.5)


if __name__ == "__main__":
    unittest.main()
