import unittest

from parsing.address_extractor import extract_address_from_lines


class AddressExtractorTests(unittest.TestCase):
    def test_extract_address_from_lines_parses_two_line_address_without_street_type_keyword(self):
        parsed = extract_address_from_lines(
            [
                "Am Röthenbacher Landgraben 2",
                "90451 Nürnberg",
            ]
        )

        self.assertEqual(
            parsed,
            {
                "street": "Am Röthenbacher Landgraben",
                "street_no": "2",
                "zip": 90451,
                "city": "Nürnberg",
            },
        )

    def test_extract_address_from_lines_rejects_company_name_as_three_line_street(self):
        parsed = extract_address_from_lines(
            [
                "REWE Markt GmbH",
                "22",
                "90763 Fürth",
            ]
        )

        self.assertIsNone(parsed)

    def test_extract_address_from_lines_keeps_regular_two_line_street_addresses(self):
        parsed = extract_address_from_lines(
            [
                "Kaiserstr. 22",
                "90763 Fürth",
            ]
        )

        self.assertEqual(
            parsed,
            {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": 90763,
                "city": "Fürth",
            },
        )


if __name__ == "__main__":
    unittest.main()

