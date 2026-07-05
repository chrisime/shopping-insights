import unittest

from bs4 import BeautifulSoup

from parsing.lidl_info_extractor import extract_lidl_receipt_info
from parsing.lidl_payment_extractor import normalize_lidl_payment_methods
from parsing.lidl_pos_extractor import infer_lidl_pos_metadata_from_receipt_id
from shared.receipt_schema import normalize_receipt_schema


class LidlInfoExtractorTests(unittest.TestCase):
    def test_infer_lidl_pos_metadata_from_receipt_id(self):
        metadata = infer_lidl_pos_metadata_from_receipt_id("230058821020240819725516")

        self.assertEqual(
            metadata,
            {
                "market": "5882",
                "register": "10",
                "cashier": "725516",
                "bon_number": "725516",
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
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["store"], "Fürth-Südstadt")
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
        self.assertEqual(receipt_data["bon_number"], "113520")

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
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["store"], "Fürth-Südstadt")
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
                    "network": "LIDL",
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

    def test_normalize_lidl_payment_methods_maps_unknown_method_to_lidl_network(self):
        payment_methods = [
            {
                "method": "Geldger├ñte",
                "amount": "4,20",
            }
        ]

        normalized = normalize_lidl_payment_methods(payment_methods)

        self.assertEqual(
            normalized,
            [
                {
                    "method": "Geldger├ñte",
                    "network": "LIDL",
                    "amount": 4.2,
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
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["sticker_discount_pct"], [20])
        self.assertEqual(receipt_data["sticker_discount"], 0.4)
        self.assertIsNone(receipt_data.get("discount"))

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
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["discount"], 0.4)
        self.assertIsNone(receipt_data.get("sticker_discount"))
        self.assertEqual(receipt_data.get("sticker_discount_pct"), [])

    def test_extract_basic_receipt_info_treats_rabatt_without_percent_as_regular_saved_amount(self):
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
            "Fürth-Südstadt",
        )

        self.assertIsNone(receipt_data.get("sticker_discount"))
        self.assertEqual(receipt_data.get("sticker_discount_pct"), [])
        self.assertEqual(receipt_data.get("discount"), 0.8)

    def test_extract_basic_receipt_info_treats_product_rabatt_as_regular_saved_amount(self):
        html = """
        <html><body>
            <span class="purchase_list">
                Cashewkerne 200g      2,89 x   3    8,67 A
                Rabatt Cashew                -1,74
                Lidl Plus Rabatt             -2,07
            </span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data.get("discount"), 1.74)
        self.assertIsNone(receipt_data.get("sticker_discount"))

    def test_extract_basic_receipt_info_defaults_lidlplus_saved_amount_to_zero(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "Fürth-Südstadt",
        )

        self.assertIsNone(receipt_data["lidlplus_discount"])

    def test_extract_basic_receipt_info_reads_branch_name_from_lidl_header(self):
        html = """
        <html><body>
            <span id="header_line_1">Fürth-Südstadt</span>
            <span id="header_line_2">Fronmüllerstr. 12</span>
            <span id="header_line_3">90763 Fürth-Südstadt</span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426420240828113520",
            "Lidl",
        )

        self.assertEqual(receipt_data["store"], "Fürth-Südstadt")
        self.assertEqual(receipt_data["address"]["city"], "Fürth-Südstadt")

    def test_extract_basic_receipt_info_keeps_store_when_header_has_no_branch_line(self):
        html = """
        <html><body>
            <span id="header_line_2">Olympiastr. 25a</span>
            <span id="header_line_3">82467 Garmisch-Partenkirchen</span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "2300679112024090991221",
            "Lidl",
        )

        self.assertEqual(receipt_data["store"], "Lidl")
        self.assertEqual(receipt_data["address"]["city"], "Garmisch-Partenkirchen")

    def test_extract_basic_receipt_info_uses_api_city_as_branch_when_header_city_differs(self):
        html = """
        <html><body>
            <span id="header_line_2">Fronmüllerstr. 12</span>
            <span id="header_line_3">90763 Fürth</span>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")

        receipt_data = extract_lidl_receipt_info(
            soup,
            "23004426220241031479702",
            "Lidl",
            {
                "street": "Fronmüllerstr.",
                "street_no": "12",
                "zip": "90763",
                "city": "Fürth-Südstadt",
            },
        )

        self.assertEqual(receipt_data["store"], "Fürth-Südstadt")
        self.assertEqual(receipt_data["address"]["city"], "Fürth")

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
            "Fürth-Südstadt",
        )

        self.assertEqual(receipt_data["total_price"], 33.7)

    def test_normalize_receipt_schema_keeps_lidl_fields_neutral_and_converts_strings(self):
        normalized = normalize_receipt_schema(
            {
                "id": "23004426420240828113520",
                "retailer": "lidl",
                "purchase_date": "28.08.2024",
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

        self.assertIn("lidlplus_discount", normalized)
        self.assertIsNone(normalized["lidlplus_discount"])
        self.assertIn("sticker_discount", normalized)
        self.assertIsNone(normalized["sticker_discount"])
        self.assertIn("sticker_discount_pct", normalized)
        # REWE fields are present but None for lidl
        self.assertIn("rewe_bonus_amount", normalized)
        self.assertIsNone(normalized["rewe_bonus_amount"])
        self.assertIn("rewe_bonus_discount", normalized)
        self.assertIsNone(normalized["rewe_bonus_discount"])
        self.assertIn("rewe_bonus_total_amount", normalized)
        self.assertIsNone(normalized["rewe_bonus_total_amount"])
        self.assertEqual(normalized["purchase_date"], "2024-08-28")
        self.assertEqual(
            normalized["address"],
            {
                "street": "Hauptstr.",
                "street_no": "12",
                "zip": 90762,
                "city": "Fürth",
            },
        )
        self.assertEqual(
            normalized["payment_methods"],
            [{"method": "Lidl Pay", "network": "LIDL", "amount": 2.78}],
        )

    def test_normalize_receipt_schema_accepts_lidl_schema_profile_from_caller(self):
        normalized = normalize_receipt_schema(
            {
                "id": "23004426420240828113520",
                "retailer": "lidl",
                "purchase_date": "28.08.2024",
                "store": "Fürth-Südstadt",
                "lidlplus_discount": "2,78",
            },
        )

        self.assertEqual(normalized["lidlplus_discount"], 2.78)
        self.assertEqual(normalized["sticker_discount_pct"], [])
        self.assertIsNone(normalized["sticker_discount"])


if __name__ == "__main__":
    unittest.main()

