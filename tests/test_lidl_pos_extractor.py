import unittest
from bs4 import BeautifulSoup

from parsing.lidl_pos_extractor import apply_lidl_pos_metadata


class LidlPosExtractorTests(unittest.TestCase):
    def test_apply_lidl_pos_metadata_extracts_from_pos_line(self):
        soup = BeautifulSoup(
            '<span id="return_code_line_13">1234 56789/12 01.01.24 14:30</span>',
            "html.parser",
        )
        result = apply_lidl_pos_metadata({}, soup, receipt_id="ignored")
        self.assertEqual(result.get("market"), "1234")
        self.assertEqual(result.get("register"), "12")
        self.assertEqual(result.get("cashier"), "56789")
        self.assertEqual(result.get("bon_number"), "56789".zfill(6))

    def test_apply_lidl_pos_metadata_falls_back_to_serial_line(self):
        soup = BeautifulSoup(
            '<span id="return_code_line_3">LDL-000-5678-99</span>',
            "html.parser",
        )
        result = apply_lidl_pos_metadata({}, soup)
        self.assertEqual(result.get("market"), "5678")
        self.assertEqual(result.get("register"), "99")

    def test_apply_lidl_pos_metadata_falls_back_to_receipt_id(self):
        soup = BeautifulSoup(
            '<span id="return_code_line_13"></span>'
            '<span id="return_code_line_3"></span>',
            "html.parser",
        )
        result = apply_lidl_pos_metadata({}, soup, receipt_id="230012340120250101123456")
        self.assertEqual(result.get("market"), "1234")
        self.assertEqual(result.get("register"), "01")
        self.assertEqual(result.get("cashier"), "123456")
        self.assertEqual(result.get("bon_number"), "123456")

    def test_apply_lidl_pos_metadata_adds_none_metadata_when_no_match(self):
        soup = BeautifulSoup("<html></html>", "html.parser")
        result = apply_lidl_pos_metadata({"existing": True}, soup)
        self.assertEqual(result["existing"], True)
        self.assertIsNone(result.get("market"))
        self.assertIsNone(result.get("register"))

    def test_apply_lidl_pos_metadata_pos_takes_precedence_over_serial_and_id(self):
        """POS line match should win over serial line and receipt ID fallback."""
        soup = BeautifulSoup(
            '<span id="return_code_line_13">9999 11111/77 01.01.24 10:00</span>'
            '<span id="return_code_line_3">LDL-000-8888-66</span>',
            "html.parser",
        )
        result = apply_lidl_pos_metadata({}, soup, receipt_id="230012340120250101123456")
        self.assertEqual(result.get("market"), "9999")
        self.assertEqual(result.get("register"), "77")
        self.assertEqual(result.get("cashier"), "11111")


if __name__ == "__main__":
    unittest.main()
