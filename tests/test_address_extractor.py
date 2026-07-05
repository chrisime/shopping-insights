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

    def test_extract_address_from_lines_rejects_company_suffix_in_three_line_address(self):
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

    def test_extract_address_from_lines_parses_two_line_address_with_spaced_house_number_suffix(self):
        parsed = extract_address_from_lines(
            [
                "Fürther Str. 221 b",
                "90429 Nürnberg",
            ]
        )

        self.assertEqual(
            parsed,
            {
                "street": "Fürther Str.",
                "street_no": "221b",
                "zip": 90429,
                "city": "Nürnberg",
            },
        )

    def test_extract_address_from_lines_accepts_street_without_known_suffix(self):
        parsed = extract_address_from_lines(
            [
                "Am Flughafen 5",
                "90411 Nürnberg",
            ]
        )

        self.assertEqual(
            parsed,
            {
                "street": "Am Flughafen",
                "street_no": "5",
                "zip": 90411,
                "city": "Nürnberg",
            },
        )

    def test_extract_address_from_lines_accepts_one_line_address(self):
        parsed = extract_address_from_lines(
            [
                "Hauptstr. 12, 90762 Fürth",
            ]
        )

        self.assertEqual(
            parsed,
            {
                "street": "Hauptstr.",
                "street_no": "12",
                "zip": 90762,
                "city": "Fürth",
            },
        )

    def test_extract_address_from_lines_accepts_one_line_address_without_comma(self):
        parsed = extract_address_from_lines(
            [
                "Musterweg 1 12345 Berlin",
            ]
        )

        self.assertEqual(
            parsed,
            {
                "street": "Musterweg",
                "street_no": "1",
                "zip": 12345,
                "city": "Berlin",
            },
        )


if __name__ == "__main__":
    unittest.main()

