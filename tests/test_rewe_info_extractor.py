import unittest

from parsing.rewe_info_extractor import REWE_BODY_MARKER, extract_rewe_receipt_info


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
        self.assertEqual(metadata["bon_number"], "7714")

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

    def test_extract_rewe_receipt_info_parses_address_from_store_like_header_line(self):
        text = """
König-Ludwig-Str. 2, 87645 Schwangau
EUR
MANDEL VEGAN 3,99 A
SUMME EUR 10,48
Geg. VISA EUR 10,48
12.10.2025 14:39 Bon-Nr.:9216
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "REWE")
        self.assertEqual(
            metadata["address"],
            {
                "street": "König-Ludwig-Str.",
                "street_no": "2",
                "zip": 87645,
                "city": "Schwangau",
            },
        )
        self.assertEqual(metadata["purchase_date"], "2025-10-12")
        self.assertEqual(metadata["id"], "rewe-12102025-1439-9216")

    def test_extract_rewe_receipt_info_parses_footer_only_address_when_header_has_none(self):
        text = """
REWE
EUR
MANDEL VEGAN 3,99 A
SUMME EUR 10,48
Geg. VISA EUR 10,48
12.10.2025 14:39 Bon-Nr.:9216
UID Nr.: DE987654321
König-Ludwig-Str. 2
87645 Schwangau
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "REWE")
        self.assertEqual(
            metadata["address"],
            {
                "street": "König-Ludwig-Str.",
                "street_no": "2",
                "zip": 87645,
                "city": "Schwangau",
            },
        )

    def test_extract_rewe_receipt_info_parses_header_address_without_comma_after_house_number(self):
        text = """
R E W E
Markt 4196
Ludwig-Erhard-Allee 12 76131 Karlsruhe
EUR
BANANE 1,99 A
SUMME EUR 1,99
Geg. VISA EUR 1,99
Markt:4196 Kasse:4 Bed.:432104
12.02.2026 11:03 Bon-Nr.:2587
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "R E W E")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Ludwig-Erhard-Allee",
                "street_no": "12",
                "zip": 76131,
                "city": "Karlsruhe",
            },
        )
        self.assertEqual(metadata["id"], "rewe-4196-4-12022026-1103-2587")

    def test_extract_rewe_receipt_info_parses_footer_address_after_uid_dash_variant(self):
        text = """
R E W E
EUR
BANANE 1,99 A
SUMME EUR 1,99
Geg. VISA EUR 1,99
12.02.2026 11:03 Bon-Nr.:2587
UID-Nr.: DE123456789
Ludwig-Erhard-Allee 12
76131 Karlsruhe
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(
            metadata["address"],
            {
                "street": "Ludwig-Erhard-Allee",
                "street_no": "12",
                "zip": 76131,
                "city": "Karlsruhe",
            },
        )

    def test_extract_rewe_receipt_info_parses_split_header_address_for_12022026_layout(self):
        text = """
R E W E
Markt 4196
Ludwig-Erhard-Allee
12
76131 Karlsruhe
EUR
JA! KOERN. FRISC 1,19 A
SUMME EUR 8,22
Geg. VISA EUR 8,22
Markt:4196 Kasse:4 Bed.:432104
12.02.2026 11:03 Bon-Nr.:2587
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "R E W E")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Ludwig-Erhard-Allee",
                "street_no": "12",
                "zip": 76131,
                "city": "Karlsruhe",
            },
        )
        self.assertEqual(metadata["market"], "4196")
        self.assertEqual(metadata["register"], "4")
        self.assertEqual(metadata["cashier"], "432104")
        self.assertEqual(metadata["id"], "rewe-4196-4-12022026-1103-2587")

    def test_extract_rewe_receipt_info_parses_real_12022026_header_with_stars_and_glued_house_number(self):
        text = """
R E W E
** Poppenreuther Str.72-74 **
** 90765 Fürth **
UID Nr.: DE811274562
EUR
JA! KOERN. FRISC 1,19 B
SUMME EUR 8,22
Geg. VISA EUR 8,22
12.02.2026 11:03 Bon-Nr.:2587
Markt:4196 Kasse:4 Bed.:432104
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "R E W E")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Poppenreuther Str.",
                "street_no": "72-74",
                "zip": 90765,
                "city": "Fürth",
            },
        )
        self.assertEqual(metadata["id"], "rewe-4196-4-12022026-1103-2587")

    def test_extract_rewe_receipt_info_parses_header_with_spaced_house_number_suffix_before_uid(self):
        text = """
REWE
Fürther Str. 221 b
90429 Nürnberg
UID Nr.: DE457418405
EUR
BANANE 1,99 A
SUMME EUR 1,99
Geg. VISA EUR 1,99
Markt:4426 Kasse:6 Bed.:123456
04.04.2026 12:30 Bon-Nr.:9876
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "REWE")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Fürther Str.",
                "street_no": "221b",
                "zip": 90429,
                "city": "Nürnberg",
            },
        )
        self.assertEqual(metadata["market"], "4426")
        self.assertEqual(metadata["register"], "6")
        self.assertEqual(metadata["cashier"], "123456")
        self.assertEqual(metadata["id"], "rewe-4426-6-04042026-1230-9876")

    def test_extract_rewe_receipt_info_does_not_use_two_line_header_address_as_store_name(self):
        text = """
REWE
Bahnhofsplatz 9
90443 Nürnberg
UID Nr.: DE457418405
EUR
SPINAT-FETA STRU 2,20 A
SUMME EUR 5,69
Geg. VISA EUR 5,69
Markt:6005 Kasse:5 Bed.:432105
09.05.2025 05:54 Bon-Nr.:7243
""".strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        metadata = extract_rewe_receipt_info(text, lines)

        self.assertEqual(metadata["store"], "REWE")
        self.assertEqual(
            metadata["address"],
            {
                "street": "Bahnhofsplatz",
                "street_no": "9",
                "zip": 90443,
                "city": "Nürnberg",
            },
        )
        self.assertEqual(metadata["market"], "6005")
        self.assertEqual(metadata["register"], "5")
        self.assertEqual(metadata["cashier"], "432105")
        self.assertEqual(metadata["bon_number"], "7243")
        self.assertEqual(metadata["id"], "rewe-6005-5-09052025-0554-7243")


    def test_rewe_body_marker_constant(self):
        self.assertEqual(REWE_BODY_MARKER, "EUR")


if __name__ == "__main__":
    unittest.main()

