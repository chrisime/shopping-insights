import unittest

from parsing.rewe_bonus_extractor import extract_bonus_amounts_from_text


class ReweBonusExtractorTests(unittest.TestCase):
    def test_extract_bonus_amounts_from_text_with_both_matches(self):
        text = (
            "Mit diesem Einkauf hast du 1,23 EUR REWE Bonus-Guthaben gesammelt:\n"
            "Aktuelles Bonus-Guthaben: 45,67 EUR"
        )
        amount, total = extract_bonus_amounts_from_text(text)
        self.assertEqual(amount, 1.23)
        self.assertEqual(total, 45.67)

    def test_extract_bonus_amounts_from_text_with_only_collected(self):
        text = (
            "Mit diesem Einkauf hast du 0,50 EUR REWE Bonus-Guthaben gesammelt:\n"
            "Kein Gesamtguthaben genannt"
        )
        amount, total = extract_bonus_amounts_from_text(text)
        self.assertEqual(amount, 0.5)
        self.assertIsNone(total)

    def test_extract_bonus_amounts_from_text_with_only_total(self):
        text = (
            "Kein sammel text hier\n"
            "Aktuelles Bonus-Guthaben: 99,99 EUR"
        )
        amount, total = extract_bonus_amounts_from_text(text)
        self.assertEqual(amount, 0.0)
        self.assertEqual(total, 99.99)

    def test_extract_bonus_amounts_from_text_with_no_matches(self):
        text = "Einkauf ohne Bonus-Informationen"
        amount, total = extract_bonus_amounts_from_text(text)
        self.assertEqual(amount, 0.0)
        self.assertIsNone(total)

    def test_extract_bonus_amounts_from_text_with_empty_string(self):
        amount, total = extract_bonus_amounts_from_text("")
        self.assertEqual(amount, 0.0)
        self.assertIsNone(total)


if __name__ == "__main__":
    unittest.main()
