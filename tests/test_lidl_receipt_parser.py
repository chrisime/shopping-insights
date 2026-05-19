import sys
import unittest
from unittest.mock import Mock, patch

import requests
import simplejson
from bs4 import BeautifulSoup

from api.lidl_client import get_lidl_ticket
from parsing.lidl_receipt_parser import parse_lidl_ticket
from parsing.lidl_validator import LidlReceiptValidationError, validate_lidl_receipt_data
from parsing.lidl_totals_preprocessor import extract_lidl_totals_input
from result_types import ReceiptParseResult
from workflows.error_mapping import render_exception_reason, render_validation_reason
from workflows.workflow_constants import REASON_KIND_LIDL_FETCH


def _fetch_lidl_receipt_parse_result(session, receipt_id: str) -> ReceiptParseResult:
    try:
        ticket_data = get_lidl_ticket(session, receipt_id)
    except requests.exceptions.HTTPError as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc, REASON_KIND_LIDL_FETCH))
    except requests.exceptions.RequestException as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc, REASON_KIND_LIDL_FETCH))
    except simplejson.JSONDecodeError as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc, REASON_KIND_LIDL_FETCH))
    except (KeyError, TypeError, ValueError) as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc))
    except Exception as exc:  # pragma: no cover - defensive fallback
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc, REASON_KIND_LIDL_FETCH))

    try:
        receipt_data = parse_lidl_ticket(ticket_data, receipt_id)
        validate_lidl_receipt_data(receipt_data)
        return ReceiptParseResult(receipt_data=receipt_data)
    except LidlReceiptValidationError as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_validation_reason(exc))
    except (KeyError, TypeError, ValueError) as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc))


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
            "date": "19.08.2024",
            "store": "Fürth-Südstadt",
            "htmlPrintedReceipt": "<html><body></body></html>",
        }

        with patch.object(sys.modules[__name__], "get_lidl_ticket", return_value=ticket_data):
            result = _fetch_lidl_receipt_parse_result(
                session,
                "230058821020240819725516",
            )

        self.assertIsNone(result.receipt_data)
        self.assertIsNotNone(result.skip_reason)
        self.assertIn("Validatorfehler:", str(result.skip_reason))
        self.assertIn("items: keine Artikel erkannt", str(result.skip_reason))

    def test_fetch_lidl_receipt_parse_result_returns_receipt_data_for_valid_receipt(self):
        session = Mock()
        ticket_data = {
            "date": "19.08.2024",
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

        with patch.object(sys.modules[__name__], "get_lidl_ticket", return_value=ticket_data):
            receipt_data = _fetch_lidl_receipt_parse_result(
                session,
                "230058821020240819725516",
            ).receipt_data

        self.assertIsNotNone(receipt_data)
        self.assertEqual(receipt_data["id"], "230058821020240819725516")
        self.assertEqual(receipt_data["purchase_date"], "2024-08-19")
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

    def test_validate_lidl_receipt_data_rejects_non_iso_purchase_date(self):
        with self.assertRaises(LidlReceiptValidationError) as context:
            validate_lidl_receipt_data(
                {
                    "id": "230058821020240819725516",
                    "retailer": "lidl",
                    "purchase_date": "19.08.2024",
                    "market": "5882",
                    "register": "10",
                    "cashier": "725516",
                    "total_price": 2.78,
                    "payment_methods": [{"method": "Lidl Pay", "network": "LIDL", "amount": 2.78}],
                    "items": [{"name": "Wasser", "price": 2.78, "quantity": 1, "unit": "stk"}],
                }
            )

        self.assertIn("purchase_date: hat nicht das erwartete Datumsformat", str(context.exception))

    def test_parse_lidl_ticket_maps_store_address_in_parsing_layer(self):
        ticket_data = {
            "date": "19.08.2024",
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

    def test_parse_lidl_ticket_extracts_address_from_split_header_line_spans(self):
        ticket_data = {
            "date": "19.08.2024",
            "store": "Lidl Nürnberg",
            "htmlPrintedReceipt": """
            <html><body>
                <span id="header_line_1"></span>
                <span id="header_line_2"></span>
                <span id="header_line_3"></span>
                <span id="header_line_4">       </span><span id="header_line_4" class="css_bold">Am Röthenbacher Landgraben 2</span><span id="header_line_4">       </span><span id="header_line_4"></span>
                <span id="header_line_5">              </span><span id="header_line_5" class="css_bold">90451 Nürnberg</span><span id="header_line_5">              </span><span id="header_line_5"></span>
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

        self.assertEqual(
            receipt_data["address"],
            {
                "street": "Am Röthenbacher Landgraben",
                "street_no": "2",
                "zip": 90451,
                "city": "Nürnberg",
            },
        )


if __name__ == "__main__":
    unittest.main()

