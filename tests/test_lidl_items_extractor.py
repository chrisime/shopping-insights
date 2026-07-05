import unittest
from bs4 import BeautifulSoup

from parsing.lidl_items_extractor import extract_lidl_receipt_items


class LidlItemsExtractorTests(unittest.TestCase):
    def test_extract_lidl_receipt_items_extracts_articles(self):
        soup = BeautifulSoup(
            '<span class="article" data-art-id="001" data-art-description="Milch" '
            'data-art-quantity="2" data-unit-price="1,19">Milch 2x 1,19</span>',
            "html.parser",
        )
        items = extract_lidl_receipt_items(soup)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "Milch")
        self.assertEqual(items[0]["price"], 1.19)
        self.assertEqual(items[0]["quantity"], 2)
        self.assertEqual(items[0]["unit"], "stk")

    def test_extract_lidl_receipt_items_detects_kg_unit(self):
        soup = BeautifulSoup(
            '<span class="article" data-art-id="002" data-art-description="Bananen" '
            'data-art-quantity="0,500" data-unit-price="2,59">Bananen 0,500 kg</span>',
            "html.parser",
        )
        items = extract_lidl_receipt_items(soup)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["unit"], "kg")

    def test_extract_lidl_receipt_items_handles_multiple_articles(self):
        soup = BeautifulSoup(
            '<span class="article" data-art-id="001" data-art-description="Brot" '
            'data-art-quantity="1" data-unit-price="2,49">Brot</span>'
            '<span class="article" data-art-id="002" data-art-description="Butter" '
            'data-art-quantity="1" data-unit-price="1,99">Butter</span>',
            "html.parser",
        )
        items = extract_lidl_receipt_items(soup)
        self.assertEqual(len(items), 2)

    def test_extract_lidl_receipt_items_skips_articles_without_description(self):
        soup = BeautifulSoup(
            '<span class="article" data-art-id="003" data-unit-price="5,00">'
            "No desc</span>",
            "html.parser",
        )
        items = extract_lidl_receipt_items(soup)
        self.assertEqual(len(items), 0)

    def test_extract_lidl_receipt_items_skips_articles_without_price(self):
        soup = BeautifulSoup(
            '<span class="article" data-art-id="004" data-art-description="Test">'
            "No price</span>",
            "html.parser",
        )
        items = extract_lidl_receipt_items(soup)
        self.assertEqual(len(items), 0)

    def test_extract_lidl_receipt_items_returns_empty_when_no_article_spans(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        self.assertEqual(extract_lidl_receipt_items(soup), [])

    def test_extract_lidl_receipt_items_detects_eur_kg_unit(self):
        soup = BeautifulSoup(
            '<span class="article" data-art-id="005" data-art-description="Äpfel" '
            'data-art-quantity="0,300" data-unit-price="3,99">Äpfel 0,300 kg EUR/kg</span>',
            "html.parser",
        )
        items = extract_lidl_receipt_items(soup)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["unit"], "kg")


if __name__ == "__main__":
    unittest.main()
