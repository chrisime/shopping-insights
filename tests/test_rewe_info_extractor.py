import unittest

from parsing.rewe_info_extractor import extract_rewe_receipt_info


class ReweInfoExtractorTests(unittest.TestCase):
    def test_extract_rewe_receipt_info_prefers_footer_company_name_over_header_address(self):
        text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
BANANE 1,99 A
SUMME EUR 1,99
Geg. VISA EUR 1,99
Markt:0605 Kasse:8 Bed.:432108
11.10.2025 13:00 Bon-Nr.:7714
Vielen Dank für deinen Einkauf!
UID Nr.: DE123456789
REWE Uwe Angl oHG
Kaiserstr. 22, 90763 Fürth
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "REWE Uwe Angl oHG")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": 90763,
                "city": "Fürth",
            },
        )
        self.assertEqual(metadata["market"], "0605")
        self.assertEqual(metadata["register"], "8")
        self.assertEqual(metadata["cashier"], "432108")

    def test_extract_rewe_receipt_info_supports_mixed_case_footer_company_names(self):
        text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
BANANE 1,99 A
SUMME EUR 1,99
Geg. VISA EUR 1,99
Markt:5802 Kasse:4 Bed.:4646
12.10.2025 14:39 Bon-Nr.:9216
UID Nr.: DE987654321
Rewe Kunkel oHG
Hauptstr. 1, 90402 Nürnberg
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "Rewe Kunkel oHG")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": 90763,
                "city": "Fürth",
            },
        )
        self.assertEqual(metadata["market"], "5802")

    def test_extract_rewe_receipt_info_falls_back_to_header_company_without_appending_market_or_address(self):
        text = """
REWE-Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
BANANE 1,99 A
SUMME EUR 1,99
Geg. VISA EUR 1,99
Markt:5802 Kasse:4 Bed.:4646
12.10.2025 14:39 Bon-Nr.:9216
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "REWE-Markt GmbH")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": 90763,
                "city": "Fürth",
            },
        )
        self.assertEqual(metadata["market"], "5802")


if __name__ == "__main__":
    unittest.main()

