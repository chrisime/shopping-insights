import unittest

from parsing.rewe_totals_extractor import extract_rewe_totals


class ReweTotalsExtractorTests(unittest.TestCase):
    def test_extract_rewe_totals_uses_raw_sum_and_bonus_redemption(self):
        result = extract_rewe_totals(
            raw_total_price=10.97,
            saved_amount=0.63,
            saved_deposit=0.96,
            rewe_bonus_saved_amount=5.0,
        )

        self.assertEqual(result.amount_saved, 0.63)
        self.assertEqual(result.saved_deposit, 0.96)
        self.assertEqual(result.additional_savings["rewe_bonus_amount_saved"], 5.0)
        self.assertEqual(result.total_price, 5.97)

    def test_extract_rewe_totals_leaves_total_empty_without_raw_sum(self):
        result = extract_rewe_totals(
            raw_total_price=None,
            saved_amount=0.63,
            saved_deposit=0.96,
            rewe_bonus_saved_amount=0.0,
        )

        self.assertEqual(result.amount_saved, 0.63)
        self.assertEqual(result.saved_deposit, 0.96)
        self.assertIsNone(result.total_price)

    def test_extract_rewe_totals_caps_negative_total_at_zero(self):
        result = extract_rewe_totals(
            raw_total_price=2.0,
            saved_amount=0.0,
            saved_deposit=0.0,
            rewe_bonus_saved_amount=5.0,
        )

        self.assertEqual(result.total_price, 0.0)
        self.assertEqual(result.additional_savings["rewe_bonus_amount_saved"], 5.0)


if __name__ == "__main__":
    unittest.main()

