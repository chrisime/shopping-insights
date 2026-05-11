import unittest
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

from parsing.lidl_receipt_parser import parse_lidl_ticket
from parsing.lidl_totals_preprocessor import extract_lidl_totals_input
from workflows.lidl_workflow import fetch_lidl_receipt_parse_result


class LidlReceiptParserTests(unittest.TestCase):
    def test_extract_lidl_totals_input_preprocesses_values_before_totals_extractor(self):
        html = """
        <html><body>
            <span class="purchase_list">Pfandrückgabe -0,25</span>
        </body></html>
        """.strip()

        totals_input = extract_lidl_totals_input(
            soup=BeautifulSoup(html, "html.parser"),
            amount_saved=0.5,
            lidlplus_amount_saved=0.25,
            sticker_discount_amount=0.1,
        )

        self.assertEqual(totals_input.amount_saved, 0.5)
        self.assertEqual(totals_input.lidlplus_amount_saved, 0.25)
        self.assertEqual(totals_input.sticker_discount_amount, 0.1)
        self.assertEqual(totals_input.saved_deposit, 0.25)

    def test_fetch_lidl_receipt_parse_result_returns_skip_reason_for_invalid_receipt(self):
        session = Mock()
        ticket_data = {
            "date": "2024-08-19T12:00:00",
            "store": "Fürth-Südstadt",
            "htmlPrintedReceipt": "<html><body></body></html>",
        }

        with patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            return_value=ticket_data,
        ):
            result = fetch_lidl_receipt_parse_result(
                session,
                "230058821020240819725516",
            )

        self.assertIsNone(result.receipt_data)
        self.assertIn("Validatorfehler:", result.skip_reason)
        self.assertIn("items: keine Artikel erkannt", result.skip_reason)

    def test_fetch_lidl_receipt_parse_result_returns_receipt_data_for_valid_receipt(self):
        session = Mock()
        ticket_data = {
            "date": "2024-08-19T12:00:00",
            "store": "Fürth-Südstadt",
            "htmlPrintedReceipt": """
            <html><body>
                <div>Lidl</div>
                <div>Hauptstr. 12</div>
                <div>90762 Fürth</div>
                <span class="article" data-art-id="1" data-art-description="Wasser" data-art-quantity="1" data-unit-price="2,78">Wasser</span>
                <span id="purchase_tender_information_3">Bezahlung Lidl Pay</span>
                <span id="purchase_tender_information_5">2,78 EUR</span>
                <span id="return_code_line_13">5882 725516/10 19.08.24 12:00</span>
            </body></html>
            """.strip(),
        }

        with patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            return_value=ticket_data,
        ):
            receipt_data = fetch_lidl_receipt_parse_result(
                session,
                "230058821020240819725516",
            ).receipt_data

        self.assertIsNotNone(receipt_data)
        self.assertEqual(receipt_data["id"], "230058821020240819725516")
        self.assertEqual(
            receipt_data["address"],
            {
                "street": "Hauptstr.",
                "street_no": "12",
                "zip": 90762,
                "city": "Fürth",
            },
        )
        self.assertEqual(receipt_data["market"], "5882")
        self.assertEqual(receipt_data["register"], "10")
        self.assertEqual(receipt_data["cashier"], "725516")
        self.assertEqual(receipt_data["total_price"], 2.78)

    def test_parse_lidl_ticket_maps_store_address_in_parsing_layer(self):
        ticket_data = {
            "date": "2024-08-19T12:00:00",
            "store": {
                "name": "Fürth-Südstadt",
                "street": "Hauptstr.",
                "houseNumber": "12",
                "postalCode": "90762",
                "city": "Fürth",
            },
            "htmlPrintedReceipt": """
            <html><body>
                <span class="article" data-art-id="1" data-art-description="Wasser" data-art-quantity="1" data-unit-price="2,78">Wasser</span>
                <span id="purchase_tender_information_3">Bezahlung Lidl Pay</span>
                <span id="purchase_tender_information_5">2,78 EUR</span>
                <span id="return_code_line_13">5882 725516/10 19.08.24 12:00</span>
            </body></html>
            """.strip(),
        }

        receipt_data = parse_lidl_ticket(
            ticket_data,
            "230058821020240819725516",
        )

        self.assertIsNotNone(receipt_data)
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


if __name__ == "__main__":
    unittest.main()

