import unittest

from bs4 import BeautifulSoup

from parsing.lidl_info_extractor import (
    extract_lidl_receipt_info,
    infer_lidl_pos_metadata_from_receipt_id,
    normalize_lidl_payment_methods,
)
from shared.receipt_schema import normalize_receipt_schema


class LidlInfoExtractorTests(unittest.TestCase):
    def test_infer_lidl_pos_metadata_from_receipt_id(self):
        metadata = infer_lidl_pos_metadata_from_receipt_id(
            "230058821020240819725516",
            "2024.08.19",
        )

        self.assertEqual(
            metadata,
            {
                "market": "5882",
                "register": "10",
                "cashier": "725516",
            },
        )

    def test_extract_basic_receipt_info_uses_id_fallback_when_html_pos_lines_missing(self):
        soup = BeautifulSoup(
            """
            <html><body>
                <div>Lidl</div>
                <div>Hauptstr. 12</div>
                <div>90762 Fürth</div>
            </body></html>
            """,
            "html.parser",
        )

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["store"], "lidl")
        self.assertEqual(
            receipt_data["address"],
            {
                "street": "Hauptstr.",
                "street_no": "12",
                "zip": 90762,
                "city": "Fürth",
            },
        )
        self.assertEqual(receipt_data["market"], "4426")
        self.assertEqual(receipt_data["register"], "04")
        self.assertEqual(receipt_data["cashier"], "113520")

    def test_html_pos_metadata_wins_over_id_fallback(self):
        html = """
        <html><body>
            <span id="return_code_line_13">4426 067583/83 02.05.26 16:21</span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["store"], "lidl")
        self.assertEqual(receipt_data["market"], "4426")
        self.assertEqual(receipt_data["register"], "83")
        self.assertEqual(receipt_data["cashier"], "067583")

    def test_normalize_lidl_payment_methods_removes_old_lidl_pay_placeholders(self):
        payment_methods = [
            {
                "method": "Lidl Pay",
                "amount": "6,76",
                "network": ":",
                "card_masked": ": 02",
                "details": ": 6.76 EUR",
            }
        ]

        normalized = normalize_lidl_payment_methods(payment_methods)

        self.assertEqual(
            normalized,
            [
                {
                    "method": "Lidl Pay",
                    "amount": 6.76,
                }
            ],
        )

    def test_normalize_lidl_payment_methods_keeps_meaningful_card_payment_fields(self):
        payment_methods = [
            {
                "method": "Kreditkarte",
                "amount": "19,23",
                "network": "VISA",
                "card_masked": "############5265 00",
                "details": "Visa kontaktlos Chip Online",
            }
        ]

        normalized = normalize_lidl_payment_methods(payment_methods)

        self.assertEqual(
            normalized,
            [
                {
                    "method": "Karte",
                    "amount": 19.23,
                    "network": "VISA",
                }
            ],
        )

    def test_extract_basic_receipt_info_keeps_sticker_discount_separate_from_regular_saved_amount(self):
        html = """
        <html><body>
            <span class="purchase_list">
                RABATT 20% -0,40
            </span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["sticker_discount_pct"], [20])
        self.assertEqual(receipt_data["sticker_discount_amount"], 0.4)
        self.assertIsNone(receipt_data.get("amount_saved"))

    def test_extract_basic_receipt_info_treats_preisvorteil_as_regular_saved_amount(self):
        html = """
        <html><body>
            <span class="purchase_list">
                Preisvorteil -0,40
            </span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["amount_saved"], 0.4)
        self.assertIsNone(receipt_data.get("sticker_discount_amount"))
        self.assertEqual(receipt_data.get("sticker_discount_pct"), [])

    def test_extract_basic_receipt_info_ignores_rabatt_amount_without_percent_for_sticker_field(self):
        html = """
        <html><body>
            <span class="purchase_list">
                Rabatt -0,80
            </span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertIsNone(receipt_data.get("sticker_discount_amount"))
        self.assertEqual(receipt_data.get("sticker_discount_pct"), [])
        self.assertIsNone(receipt_data.get("amount_saved"))

    def test_extract_basic_receipt_info_defaults_lidlplus_saved_amount_to_zero(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["lidlplus_amount_saved"], 0.0)

    def test_extract_basic_receipt_info_applies_total_price_from_zu_zahlen_summary(self):
        html = """
        <html><body>
            <div>
                <span id="purchase_summary_1">zu zahlen</span>
                <span class="css_bold">33,70</span>
            </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "2024.08.28",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["total_price"], 33.7)

    def test_normalize_receipt_schema_defaults_lidlplus_saved_amount_to_zero_and_converts_strings(self):
        normalized = normalize_receipt_schema(
            {
                "id": "23004426420240828113520",
                "retailer": "lidl",
                "purchase_date": "2024.08.28",
                "store": "Fürth-Südstadt",
                "address": {
                    "street": "Hauptstr.",
                    "street_no": "12",
                    "zip": "90762",
                    "city": "Fürth",
                },
                "total_price": "2,78",
                "payment_methods": [{"method": "Lidl Pay", "amount": "2,78"}],
                "items": [
                    {"name": "Wasser", "price": "2,78", "quantity": "1", "unit": "stk"},
                    {"name": "Tomaten", "price": "3,99", "quantity": "0,696", "unit": "kg"},
                ],
            }
        )

        self.assertEqual(normalized["lidlplus_amount_saved"], 0.0)
        self.assertEqual(normalized["store"], "lidl")
        self.assertEqual(
            normalized["address"],
            {
                "street": "Hauptstr.",
                "street_no": "12",
                "zip": 90762,
                "city": "Fürth",
            },
        )
        self.assertEqual(normalized["total_price"], 2.78)
        self.assertEqual(normalized["payment_methods"][0]["amount"], 2.78)
        self.assertEqual(normalized["items"][0]["price"], 2.78)
        self.assertEqual(normalized["items"][0]["quantity"], 1)
        self.assertEqual(normalized["items"][1]["price"], 3.99)
        self.assertEqual(normalized["items"][1]["quantity"], 0.696)


if __name__ == "__main__":
    unittest.main()

