import unittest

from parsing.dm_pdf_items_extractor import (
    MULTI_ITEM_RE,
    SINGLE_ITEM_RE,
    _parse_dm_item_lines,
    _parse_item_line,
)


class ParseDmPdfItemLineTests(unittest.TestCase):
    def test_parses_single_item_line(self):
        item = _parse_item_line("dmBio Buchweizenmehl 500 g 1,95 2")
        if item is None:
            self.fail("expected item")
        self.assertEqual(item["name"], "dmBio Buchweizenmehl 500 g")
        self.assertEqual(item["price"], 1.95)
        self.assertEqual(item["quantity"], 1)
        self.assertEqual(item["unit"], "stk")

    def test_parses_single_item_with_trailing_star(self):
        item = _parse_item_line("dmBio Punschgewürz Tee 30g* 1,45 2")
        if item is None:
            self.fail("expected item")
        self.assertEqual(item["name"], "dmBio Punschgewürz Tee 30g*")
        self.assertEqual(item["price"], 1.45)

    def test_parses_multi_quantity_item(self):
        item = _parse_item_line("3x 1,75 dmBio Buchweizenmehl 5 5,25 2")
        if item is None:
            self.fail("expected item")
        self.assertEqual(item["name"], "dmBio Buchweizenmehl 5")
        self.assertEqual(item["price"], 1.75)
        self.assertEqual(item["quantity"], 3)
        self.assertEqual(item["unit"], "stk")

    def test_parses_multi_quantity_with_name_trailing_number(self):
        item = _parse_item_line("2x 5,95 Listerine Total Care 7 11,90 1")
        if item is None:
            self.fail("expected item")
        self.assertEqual(item["name"], "Listerine Total Care 7")
        self.assertEqual(item["quantity"], 2)
        self.assertEqual(item["price"], 5.95)

    def test_returns_none_for_discount_line(self):
        self.assertIsNone(_parse_item_line("4 x Coupon 20% Ernährung -1,32"))

    def test_returns_none_for_coupon_line(self):
        self.assertIsNone(_parse_item_line("Coupon fit Spülmittel -1,95"))

    def test_returns_none_for_sum_line(self):
        self.assertIsNone(_parse_item_line("SUMME EUR 5,28"))

    def test_returns_none_for_subtotal_line(self):
        self.assertIsNone(_parse_item_line("Zwischensumme 6,60"))

    def test_returns_none_for_payment_line(self):
        self.assertIsNone(_parse_item_line("VISA EUR -5,28"))

    def test_returns_none_for_header_line(self):
        self.assertIsNone(_parse_item_line("29.08.2023 17:43 2749/2 322918/1 5377"))

    def test_returns_none_for_payback_line(self):
        self.assertIsNone(_parse_item_line("2 PAYBACK Punkte erhalten"))

    def test_returns_none_for_tax_table_line(self):
        self.assertIsNone(_parse_item_line("2=7,00% 3,80 3,55 0,25"))


class ParseDmPdfItemLinesTests(unittest.TestCase):
    def test_extracts_only_item_lines(self):
        lines = [
            "29.08.2023 17:43 2749/2 322918/1 5377",
            "dmBio Buchweizenmehl 500 g 1,95 2",
            "3x 1,75 dmBio Buchweizenmehl 5 5,25 2",
            "Zwischensumme 6,60",
            "dm-Rabatte auf rabattfähige Artikel",
            "4 x Coupon 20% Ernährung -1,32",
            "SUMME EUR 5,28",
            "VISA EUR -5,28",
        ]
        items = _parse_dm_item_lines(lines)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["name"], "dmBio Buchweizenmehl 500 g")
        self.assertEqual(items[1]["name"], "dmBio Buchweizenmehl 5")
        self.assertEqual(items[1]["quantity"], 3)


class RegexSanityTests(unittest.TestCase):
    def test_multi_item_regex_matches_quantity_format(self):
        self.assertIsNotNone(MULTI_ITEM_RE.match("2x 1,95 dmBio Buchweizenmehl 5 3,90 2"))

    def test_single_item_regex_matches_plain_line(self):
        self.assertIsNotNone(SINGLE_ITEM_RE.match("dmBio Haferkleie mit Keim 500g 1,85 2"))


if __name__ == "__main__":
    unittest.main()