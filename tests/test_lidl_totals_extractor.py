import unittest

from bs4 import BeautifulSoup

from parsing.lidl_totals_extractor import extract_lidl_totals


class LidlTotalsExtractorTests(unittest.TestCase):
    def test_extract_lidl_totals_combines_known_savings_and_pfand(self):
        soup = BeautifulSoup(
            '<html><body><span class="purchase_list">Pfandrückgabe -0,25</span></body></html>',
            "html.parser",
        )

        result = extract_lidl_totals(
            soup,
            discount=0.5,
            lidlplus_discount=0.25,
            sticker_discount=0.1,
        )

        self.assertEqual(result.discount, 0.5)
        self.assertEqual(result.saved_deposit, 0.25)
        self.assertIsNone(result.total_price)
        self.assertEqual(result.additional_savings["lidlplus_discount"], 0.25)
        self.assertEqual(result.additional_savings["sticker_discount"], 0.1)

    def test_extract_lidl_totals_falls_back_to_pfand_calculation_lines(self):
        soup = BeautifulSoup(
            '<html><body><span class="purchase_list">2 x -0,08</span></body></html>',
            "html.parser",
        )

        result = extract_lidl_totals(soup)

        self.assertEqual(result.saved_deposit, 0.16)
        self.assertIsNone(result.total_price)

    def test_extract_lidl_totals_handles_no_pfand(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        result = extract_lidl_totals(soup, discount=1.0)

        self.assertEqual(result.discount, 1.0)
        self.assertIsNone(result.total_price)
        self.assertIsNone(result.saved_deposit)


if __name__ == "__main__":
    unittest.main()
