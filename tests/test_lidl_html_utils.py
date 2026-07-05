import unittest
from bs4 import BeautifulSoup

from parsing.lidl_html_utils import extract_text_from_repeated_id, extract_money_from_repeated_id


class LidlHtmlUtilsTests(unittest.TestCase):
    def test_extract_text_from_repeated_id_joins_multiple_elements(self):
        soup = BeautifulSoup(
            '<span id="foo">Hello</span><span id="foo">World</span>',
            "html.parser",
        )
        self.assertEqual(extract_text_from_repeated_id(soup, "foo"), "Hello World")

    def test_extract_text_from_repeated_id_returns_empty_string_when_no_match(self):
        soup = BeautifulSoup("<span>no id</span>", "html.parser")
        self.assertEqual(extract_text_from_repeated_id(soup, "missing"), "")

    def test_extract_text_from_repeated_id_strips_whitespace(self):
        soup = BeautifulSoup(
            '<span id="a">  foo  </span><span id="a">  bar  </span>',
            "html.parser",
        )
        self.assertEqual(extract_text_from_repeated_id(soup, "a"), "foo bar")

    def test_extract_money_from_repeated_id_parses_german_float(self):
        soup = BeautifulSoup(
            '<span id="price">1,99</span>',
            "html.parser",
        )
        self.assertEqual(extract_money_from_repeated_id(soup, "price"), 1.99)

    def test_extract_money_from_repeated_id_returns_none_for_non_numeric(self):
        soup = BeautifulSoup(
            '<span id="text">keine Zahl</span>',
            "html.parser",
        )
        self.assertIsNone(extract_money_from_repeated_id(soup, "text"))

    def test_extract_money_from_repeated_id_returns_none_when_id_missing(self):
        soup = BeautifulSoup("<span>nothing</span>", "html.parser")
        self.assertIsNone(extract_money_from_repeated_id(soup, "missing"))


if __name__ == "__main__":
    unittest.main()
