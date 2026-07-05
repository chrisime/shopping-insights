import unittest

from parsing.rewe_payment_extractor import extract_payment_methods_from_lines


class RewePaymentExtractorTests(unittest.TestCase):
    def test_extract_payment_methods_from_lines_parses_card_payment(self):
        lines = ["Geg. EC-Karte EUR 23,50"]
        methods, bonus = extract_payment_methods_from_lines(lines)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["method"], "Karte")
        self.assertEqual(methods[0]["network"], "REWE")
        self.assertEqual(bonus, 0.0)

    def test_extract_payment_methods_from_lines_detects_bonus_payment(self):
        lines = ["Geg. Bonus-Guthaben EUR 5,00"]
        methods, bonus = extract_payment_methods_from_lines(lines)
        self.assertEqual(len(methods), 1)
        self.assertEqual(bonus, 5.0)

    def test_extract_payment_methods_from_lines_handles_multiple_methods(self):
        lines = [
            "Geg. EC-Karte EUR 30,00",
            "Geg. Bonus-Guthaben EUR 2,50",
            "Geg. Bar EUR 5,00",
        ]
        methods, bonus = extract_payment_methods_from_lines(lines)
        self.assertEqual(len(methods), 3)
        self.assertEqual(bonus, 2.5)

    def test_extract_payment_methods_from_lines_skips_non_matching_lines(self):
        lines = [
            "SUMME EUR 35,00",
            "MwSt. 19% aus 29,41",
        ]
        methods, bonus = extract_payment_methods_from_lines(lines)
        self.assertEqual(len(methods), 0)
        self.assertEqual(bonus, 0.0)

    def test_extract_payment_methods_from_lines_with_negative_amount(self):
        lines = ["Geg. EC-Karte EUR -10,00"]
        methods, bonus = extract_payment_methods_from_lines(lines)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["amount"], -10.0)

    def test_extract_payment_methods_from_lines_returns_empty_for_empty_list(self):
        methods, bonus = extract_payment_methods_from_lines([])
        self.assertEqual(len(methods), 0)
        self.assertEqual(bonus, 0.0)


if __name__ == "__main__":
    unittest.main()
