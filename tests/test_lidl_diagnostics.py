import unittest
from unittest.mock import Mock, patch

from workflows.lidl_workflow import fetch_lidl_receipt_parse_result


class LidlDiagnosticsTests(unittest.TestCase):
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

    def test_fetch_lidl_receipt_parse_result_maps_store_address_in_workflow_layer(self):
        session = Mock()
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

        with patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            return_value=ticket_data,
        ):
            receipt_data = fetch_lidl_receipt_parse_result(
                session,
                "230058821020240819725516",
            ).receipt_data

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

    def test_fetch_lidl_receipt_parse_result_converts_fetch_errors_to_skip_reason(self):
        session = Mock()
        with patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            side_effect=ValueError("kaputt"),
        ):
            result = fetch_lidl_receipt_parse_result(session, "abc")

        self.assertIsNone(result.receipt_data)
        self.assertEqual(result.skip_reason, "kaputt")


if __name__ == "__main__":
    unittest.main()

