import unittest

from bs4 import BeautifulSoup

from parsing.lidl_totals_extractor import extract_lidl_totals
from parsing.lidl_totals_preprocessor import extract_lidl_totals_input


class LidlTotalsExtractorTests(unittest.TestCase):
    def test_extract_lidl_totals_combines_items_known_savings_and_pfand(self):
        soup = BeautifulSoup(
            '<html><body><span class="purchase_list">Pfandrückgabe -0,25</span></body></html>',
            "html.parser",
        )
        items = [
            {"name": "Tomaten", "price": 3.99, "quantity": 0.696},
            {"name": "Wasser", "price": 2.78, "quantity": 1},
        ]

        totals_input = extract_lidl_totals_input(
            soup,
            items,
            amount_saved=0.5,
            lidlplus_amount_saved=0.25,
            sticker_discount_amount=0.1,
        )

        result = extract_lidl_totals(
            total_no_saving=totals_input.total_no_saving,
            amount_saved=totals_input.amount_saved,
            lidlplus_amount_saved=totals_input.lidlplus_amount_saved,
            sticker_discount_amount=totals_input.sticker_discount_amount,
            saved_deposit=totals_input.saved_deposit,
        )

        self.assertEqual(result.total_price_no_saving, 5.56)
        self.assertEqual(result.amount_saved, 0.5)
        self.assertEqual(result.saved_deposit, 0.25)
        self.assertEqual(result.total_savings, 1.1)
        self.assertEqual(result.total_price, 4.46)
        self.assertEqual(result.additional_savings["lidlplus_amount_saved"], 0.25)
        self.assertEqual(result.additional_savings["sticker_discount_amount"], 0.1)

    def test_extract_lidl_totals_falls_back_to_pfand_calculation_lines(self):
        soup = BeautifulSoup(
            '<html><body><span class="purchase_list">2 x -0,08</span></body></html>',
            "html.parser",
        )

        totals_input = extract_lidl_totals_input(
            soup,
            [{"name": "Dose", "price": 1.0, "quantity": 1}],
        )

        result = extract_lidl_totals(
            total_no_saving=totals_input.total_no_saving,
            amount_saved=totals_input.amount_saved,
            lidlplus_amount_saved=totals_input.lidlplus_amount_saved,
            sticker_discount_amount=totals_input.sticker_discount_amount,
            saved_deposit=totals_input.saved_deposit,
        )

        self.assertEqual(result.saved_deposit, 0.16)
        self.assertEqual(result.total_price_no_saving, 1.0)
        self.assertEqual(result.total_price, 0.84)

    def test_extract_lidl_totals_leaves_total_price_empty_when_final_paid_is_not_positive(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        totals_input = extract_lidl_totals_input(
            soup,
            [{"name": "Gratisprobe", "price": 1.0, "quantity": 1}],
            amount_saved=1.0,
        )

        result = extract_lidl_totals(
            total_no_saving=totals_input.total_no_saving,
            amount_saved=totals_input.amount_saved,
            lidlplus_amount_saved=totals_input.lidlplus_amount_saved,
            sticker_discount_amount=totals_input.sticker_discount_amount,
            saved_deposit=totals_input.saved_deposit,
        )

        self.assertEqual(result.total_price_no_saving, 1.0)
        self.assertEqual(result.total_savings, 1.0)
        self.assertIsNone(result.total_price)


if __name__ == "__main__":
    unittest.main()

