import sys
import unittest
from unittest.mock import Mock, patch

import requests
import simplejson

from api.lidl_client import get_lidl_ticket
from parsing.lidl_receipt_parser import parse_lidl_ticket
from parsing.lidl_validator import LidlReceiptValidationError, validate_lidl_receipt_data
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


class LidlDiagnosticsTests(unittest.TestCase):
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

    def test_fetch_lidl_receipt_parse_result_maps_store_address_in_workflow_layer(self):
        session = Mock()
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

        with patch.object(sys.modules[__name__], "get_lidl_ticket", return_value=ticket_data):
            receipt_data = _fetch_lidl_receipt_parse_result(
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
        with patch.object(sys.modules[__name__], "get_lidl_ticket", side_effect=ValueError("kaputt")):
            result = _fetch_lidl_receipt_parse_result(session, "abc")

        self.assertIsNone(result.receipt_data)
        self.assertEqual(result.skip_reason, "kaputt")


if __name__ == "__main__":
    unittest.main()

