import unittest
from bs4 import BeautifulSoup

from parsing.lidl_payment_extractor import extract_lidl_payment_methods


class LidlPaymentExtractorTests(unittest.TestCase):
    def test_extract_lidl_payment_methods_from_summary_tender(self):
        soup = BeautifulSoup(
            '<span data-tender-description="true">EC-Karte</span>'
            '<span id="purchase_summary_3">25,00</span>',
            "html.parser",
        )
        methods = extract_lidl_payment_methods(soup)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["method"], "Karte")
        self.assertEqual(methods[0]["network"], "LIDL")

    def test_extract_lidl_payment_methods_skips_amount_lines(self):
        """Lines with amounts in tender-description are skipped, yielding no method."""
        soup = BeautifulSoup(
            '<span data-tender-description="true">0,50</span>'
            '<span id="purchase_summary_3">5,00</span>',
            "html.parser",
        )
        methods = extract_lidl_payment_methods(soup)
        self.assertEqual(len(methods), 0)

    def test_extract_lidl_payment_methods_uses_tender_information_fallback(self):
        soup = BeautifulSoup(
            '<span id="purchase_tender_information_3">Bezahlung Visa</span>'
            '<span id="purchase_tender_information_5">42,00</span>',
            "html.parser",
        )
        methods = extract_lidl_payment_methods(soup)
        self.assertEqual(len(methods), 1)
        self.assertIn("method", methods[0])
        self.assertEqual(methods[0]["network"], "VISA")

    def test_extract_lidl_payment_methods_normalizes_card_methods(self):
        soup = BeautifulSoup(
            '<span data-tender-description="true">Karte</span>'
            '<span id="purchase_summary_3">15,00</span>',
            "html.parser",
        )
        methods = extract_lidl_payment_methods(soup)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["method"], "Karte")
        self.assertEqual(methods[0]["network"], "LIDL")

    def test_extract_lidl_payment_methods_returns_empty_list_when_no_data(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        self.assertEqual(extract_lidl_payment_methods(soup), [])


if __name__ == "__main__":
    unittest.main()
