import unittest

from parsing.rewe_totals_extractor import extract_rewe_totals


class ReweTotalsExtractorTests(unittest.TestCase):
    def test_extract_rewe_totals_uses_raw_sum_and_bonus_redemption(self):
        result = extract_rewe_totals(
            raw_total_price=10.97,
            total_no_saving=12.56,
            saved_amount=0.63,
            saved_pfand=0.96,
            rewe_bonus_saved_amount=5.0,
        )

        self.assertEqual(result.total_price_no_saving, 12.56)
        self.assertEqual(result.amount_saved, 0.63)
        self.assertEqual(result.saved_deposit, 0.96)
        self.assertEqual(result.total_savings, 6.59)
        self.assertEqual(result.additional_savings["rewe_bonus_amount_saved"], 5.0)
        self.assertEqual(result.total_price, 5.97)

    def test_extract_rewe_totals_falls_back_to_item_totals_without_raw_sum(self):
        result = extract_rewe_totals(
            raw_total_price=None,
            total_no_saving=12.56,
            saved_amount=0.63,
            saved_pfand=0.96,
            rewe_bonus_saved_amount=0.0,
        )

        self.assertEqual(result.total_price_no_saving, 12.56)
        self.assertEqual(result.amount_saved, 0.63)
        self.assertEqual(result.saved_deposit, 0.96)
        self.assertEqual(result.total_savings, 1.59)
        self.assertEqual(result.total_price, 10.97)

    def test_extract_rewe_totals_caps_negative_total_at_zero(self):
        result = extract_rewe_totals(
            raw_total_price=2.0,
            total_no_saving=2.0,
            saved_amount=0.0,
            saved_pfand=0.0,
            rewe_bonus_saved_amount=5.0,
        )

        self.assertEqual(result.total_price, 0.0)
        self.assertEqual(result.additional_savings["rewe_bonus_amount_saved"], 5.0)


if __name__ == "__main__":
    unittest.main()

