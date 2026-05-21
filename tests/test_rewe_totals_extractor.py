import unittest

from parsing.rewe_ebons_parser import _calculate_total_price


class ReweTotalsTests(unittest.TestCase):
    def test_calculate_total_price_subtracts_bonus(self):
        self.assertEqual(_calculate_total_price(10.97, 5.0), 5.97)

    def test_calculate_total_price_none_when_no_raw(self):
        self.assertIsNone(_calculate_total_price(None, 0.0))

    def test_calculate_total_price_caps_at_zero(self):
        self.assertEqual(_calculate_total_price(2.0, 5.0), 0.0)


if __name__ == "__main__":
    unittest.main()
