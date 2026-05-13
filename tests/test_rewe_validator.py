import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import get_receipt_schema_profile
from parsing.rewe_pdf_parser import parse_rewe_receipt_pdf
from parsing.rewe_validator import (
    ReweReceiptValidationError,
    ReweValidationIssue,
    validate_rewe_receipt_data,
)
from result_types import ReceiptParseResult
from shared.receipt_schema import normalize_receipt_schema
from workflows.error_mapping import render_exception_reason, render_validation_reason
from workflows.workflow_constants import REASON_KIND_REWE_PDF_PARSE


def _parse_rewe_receipt_pdf_with_result(pdf_path: Path) -> ReceiptParseResult:
    path = Path(pdf_path)
    try:
        receipt_data = parse_rewe_receipt_pdf(path)
        validate_rewe_receipt_data(receipt_data)
        return ReceiptParseResult(receipt_data=receipt_data)
    except ReweReceiptValidationError as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_validation_reason(exc))
    except ValueError as exc:
        return ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(exc))
    except Exception as exc:  # pragma: no cover - filesystem/pdfplumber dependent
        return ReceiptParseResult(
            receipt_data=None,
            skip_reason=render_exception_reason(exc, REASON_KIND_REWE_PDF_PARSE),
        )


class ReweValidatorTests(unittest.TestCase):
    def test_validator_accepts_valid_receipt(self):
        receipt = {
            "id": "rewe-0605-8-01042026-1908-7714",
            "retailer": "rewe",
            "purchase_date": "2026.04.01",
            "total_price": 1.0,
            "rewe_bonus_amount": 0.30,
            "rewe_bonus_total_amount": 15.93,
            "market": "0605",
            "register": "8",
            "cashier": "432108",
            "payment_methods": [{"method": "Karte", "network": "VISA", "amount": 1.0}],
            "items": [{"name": "ROTWEINGLAS X2", "price": 22.95, "quantity": 1, "unit": "stk"}],
        }

        validate_rewe_receipt_data(receipt)

    def test_validator_rejects_positive_total_without_payment_methods(self):
        receipt = {
            "id": "rewe-0605-8-01042026-1908-7714",
            "retailer": "rewe",
            "purchase_date": "2026.04.01",
            "total_price": 1.0,
            "market": "0605",
            "register": "8",
            "cashier": "432108",
            "payment_methods": [],
            "items": [{"name": "ROTWEINGLAS X2", "price": 22.95, "quantity": 1, "unit": "stk"}],
        }

        with self.assertRaises(ReweReceiptValidationError) as context:
            validate_rewe_receipt_data(receipt)

        self.assertEqual(
            context.exception.issues,
            [
                ReweValidationIssue(
                    field="payment_methods",
                    reason="fehlen trotz positivem Gesamtbetrag",
                    expected="mindestens eine Zahlungsmethode bei Gesamtbetrag > 0",
                    actual="[]",
                )
            ],
        )
        self.assertIn("REWE-Bonvalidierung fehlgeschlagen:", str(context.exception))
        self.assertIn("payment_methods: fehlen trotz positivem Gesamtbetrag", str(context.exception))

    def test_validator_rejects_register_mismatch_against_receipt_id(self):
        receipt = {
            "id": "rewe-0605-8-01042026-1908-7714",
            "retailer": "rewe",
            "purchase_date": "2026.04.01",
            "total_price": 1.0,
            "market": "0605",
            "register": "14",
            "cashier": "432108",
            "payment_methods": [{"method": "Karte", "network": "VISA", "amount": 1.0}],
            "items": [{"name": "ROTWEINGLAS X2", "price": 22.95, "quantity": 1, "unit": "stk"}],
        }

        with self.assertRaises(ReweReceiptValidationError) as context:
            validate_rewe_receipt_data(receipt)

        self.assertEqual(
            context.exception.issues,
            [
                ReweValidationIssue(
                    field="register",
                    reason="passt nicht zur Receipt-ID",
                    expected="8",
                    actual="14",
                )
            ],
        )
        self.assertIn("register: passt nicht zur Receipt-ID", str(context.exception))
        self.assertIn("erwartet=8", str(context.exception))
        self.assertIn("bekommen=14", str(context.exception))

    def test_parse_rewe_receipt_pdf_with_result_returns_none_for_invalid_format(self):
        invalid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
ROTWEINGLAS X2 22,95 A
SUMME EUR 1,00
Markt:0605 Kasse:14 Bed.:432114
Datum: 01.04.2026
Uhrzeit: 19:06 Uhr
Bon-Nr.:1845
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "invalid-rewe.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=invalid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNone(receipt)

    def test_parse_rewe_receipt_pdf_with_result_exposes_skip_reason(self):
        invalid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
ROTWEINGLAS X2 22,95 A
SUMME EUR 1,00
Markt:0605 Kasse:14 Bed.:432114
Datum: 01.04.2026
Uhrzeit: 19:06 Uhr
Bon-Nr.:1845
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "invalid-rewe.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=invalid_text):
                parse_result = _parse_rewe_receipt_pdf_with_result(pdf_path)

        self.assertIsNone(parse_result.receipt_data)
        self.assertIsNotNone(parse_result.skip_reason)
        skip_reason = str(parse_result.skip_reason)
        self.assertIn("Validatorfehler:", skip_reason)
        self.assertIn("payment_methods: fehlen trotz positivem Gesamtbetrag", skip_reason)

    def test_parse_rewe_receipt_pdf_extracts_bonus_amounts(self):
        valid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
ROTWEINGLAS X2 22,95 A
-----
SUMME EUR 1,00
Geg. VISA EUR 1,00
Markt:0605 Kasse:8 Bed.:432108
01.04.2026 19:08 Bon-Nr.:7714
Mit diesem Einkauf hast du 0,30 EUR
REWE Bonus-Guthaben gesammelt:
Bonus-Aktion(en) 0,30 EUR
Aktuelles Bonus-Guthaben: 15,93 EUR
Einfach beim nächsten Einkauf einlösen!
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "valid-rewe.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=valid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(
            receipt["address"],
            {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": 90763,
                "city": "Fürth",
            },
        )
        self.assertEqual(receipt["rewe_bonus_amount"], 0.30)
        self.assertEqual(receipt["rewe_bonus_total_amount"], 15.93)
        self.assertEqual(receipt["rewe_bonus_amount_saved"], 0.0)

    def test_parse_rewe_receipt_pdf_extracts_redeemed_bonus_and_corrects_total_price(self):
        valid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
EIER BH M-L 10,97 A
-----
SUMME EUR 10,97
Geg. Bonus-Guthaben EUR 5,00
Geg. VISA EUR 5,97
Markt:0605 Kasse:13 Bed.:432113
10.03.2026 19:03 Bon-Nr.:4479
Mit diesem Einkauf hast du 0,10 EUR
REWE Bonus-Guthaben gesammelt:
Bonus-Aktion(en) 0,10 EUR
Aktuelles Bonus-Guthaben: 0,14 EUR
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "rewe-bonus-redeemed.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=valid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["total_price"], 5.97)
        self.assertEqual(receipt["rewe_bonus_amount_saved"], 5.0)
        self.assertEqual(
            receipt["payment_methods"],
            [
                {"method": "Bonus-Guthaben", "network": "REWE", "amount": 5.0},
                {"method": "Karte", "network": "VISA", "amount": 5.97},
            ],
        )

    def test_parse_rewe_receipt_pdf_normalizes_item_quantity_for_kg_and_stk(self):
        valid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
BANANEN 1,39 A
0,696 kg x 1,99 EUR/kg
APFEL 2,49 A
-----
SUMME EUR 3,88
Geg. VISA EUR 3,88
Markt:0605 Kasse:8 Bed.:432108
01.04.2026 19:08 Bon-Nr.:7714
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "rewe-quantity.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=valid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["items"][0]["quantity"], 0.696)
        self.assertEqual(receipt["items"][0]["unit"], "kg")
        self.assertEqual(receipt["items"][1]["quantity"], 1)
        self.assertEqual(receipt["items"][1]["unit"], "stk")

    def test_parse_rewe_receipt_pdf_accepts_whitespace_variant_in_market_line(self):
        valid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
BANANE 1,99 A
-----
SUMME EUR 1,99
Geg. VISA EUR 1,99
12.10.2025 14:39 Bon-Nr.:9216
Markt:5802 Kasse:4 Bed.: 4646
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "rewe-12102025.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=valid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["id"], "rewe-5802-4-12102025-1439-9216")
        self.assertEqual(receipt["purchase_date"], "2025.10.12")
        self.assertEqual(receipt["market"], "5802")
        self.assertEqual(receipt["register"], "4")
        self.assertEqual(receipt["cashier"], "4646")

    def test_parse_rewe_receipt_pdf_accepts_extra_spaces_around_bon_number(self):
        valid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
BANANE 1,99 A
-----
SUMME EUR 1,99
Geg. VISA EUR 1,99
12.10.2025 14:39 Bon-Nr.: 9216
Markt : 5802   Kasse : 4   Bed. : 4646
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "rewe-12102025-spaces.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=valid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["id"], "rewe-5802-4-12102025-1439-9216")
        self.assertEqual(receipt["market"], "5802")
        self.assertEqual(receipt["register"], "4")
        self.assertEqual(receipt["cashier"], "4646")

    def test_parse_rewe_receipt_pdf_defaults_bonus_amount_to_zero(self):
        valid_text = """
REWE Markt GmbH
Kaiserstr. 22, 90763 Fürth
EUR
ROTWEINGLAS X2 22,95 A
-----
SUMME EUR 1,00
Geg. VISA EUR 1,00
Markt:0605 Kasse:8 Bed.:432108
01.04.2026 19:08 Bon-Nr.:7714
Aktuelles Bonus-Guthaben: 15,93 EUR
Einfach beim nächsten Einkauf einlösen!
""".strip()

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = Path(tmp_dir) / "valid-rewe-no-bonus-earned.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")
            with patch("parsing.rewe_pdf_parser.extract_text_from_pdf", return_value=valid_text):
                receipt = _parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["rewe_bonus_amount"], 0.0)
        self.assertEqual(receipt["rewe_bonus_amount_saved"], 0.0)
        self.assertEqual(receipt["rewe_bonus_total_amount"], 15.93)

    def test_normalize_receipt_schema_keeps_rewe_bonus_fields_neutral_and_converts_strings(self):
        normalized = normalize_receipt_schema(
            {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": "2026.04.01",
                "store": "REWE-Markt GmbH",
                "address": {
                    "street": "Kaiserstr.",
                    "street_no": "22",
                    "zip": "90763",
                    "city": "Fürth",
                },
                "total_price": "1,00",
                "payment_methods": [{"method": "VISA", "amount": "1,00"}],
                "items": [
                    {"name": "ROTWEINGLAS X2", "price": "22,95", "quantity": "1", "unit": "stk"},
                    {"name": "BANANEN", "price": "1,99", "quantity": "0,696", "unit": "kg"},
                ],
            }
        )

        self.assertNotIn("rewe_bonus_amount", normalized)
        self.assertNotIn("rewe_bonus_amount_saved", normalized)
        self.assertNotIn("rewe_bonus_total_amount", normalized)
        self.assertNotIn("lidlplus_amount_saved", normalized)
        self.assertNotIn("sticker_discount_amount", normalized)
        self.assertNotIn("sticker_discount_pct", normalized)
        self.assertEqual(
            normalized["address"],
            {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": 90763,
                "city": "Fürth",
            },
        )
        self.assertEqual(normalized["total_price"], 1.0)
        self.assertEqual(normalized["payment_methods"][0]["method"], "Karte")
        self.assertEqual(normalized["payment_methods"][0]["network"], "VISA")
        self.assertEqual(normalized["payment_methods"][0]["amount"], 1.0)
        self.assertEqual(normalized["items"][0]["price"], 22.95)
        self.assertEqual(normalized["items"][0]["quantity"], 1)
        self.assertEqual(normalized["items"][1]["quantity"], 0.696)

    def test_normalize_receipt_schema_accepts_rewe_schema_profile_from_caller(self):
        normalized = normalize_receipt_schema(
            {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": "2026.04.01",
                "rewe_bonus_amount": "1,25",
            },
            profile=get_receipt_schema_profile("rewe"),
        )

        self.assertEqual(normalized["rewe_bonus_amount"], 1.25)
        self.assertIsNone(normalized["rewe_bonus_amount_saved"])
        self.assertIsNone(normalized["rewe_bonus_total_amount"])

    def test_normalize_receipt_schema_assigns_rewe_network_to_bonus_guthaben(self):
        normalized = normalize_receipt_schema(
            {
                "id": "rewe-0605-13-10032026-1903-4479",
                "retailer": "rewe",
                "purchase_date": "2026.03.10",
                "payment_methods": [{"method": "Bonus-Guthaben", "amount": "5,00"}],
            }
        )

        self.assertEqual(
            normalized["payment_methods"],
            [{"method": "Bonus-Guthaben", "network": "REWE", "amount": 5.0}],
        )

    def test_normalize_receipt_schema_maps_unknown_rewe_payment_method_to_rewe_network(self):
        normalized = normalize_receipt_schema(
            {
                "id": "rewe-0605-13-10032026-1903-4479",
                "retailer": "rewe",
                "purchase_date": "2026.03.10",
                "payment_methods": [{"method": "Inflationsprämie", "amount": "5,00"}],
            }
        )

        self.assertEqual(
            normalized["payment_methods"],
            [{"method": "Inflationsprämie", "network": "REWE", "amount": 5.0}],
        )

    def test_normalize_receipt_schema_keeps_existing_rewe_purchase_date_format(self):
        normalized = normalize_receipt_schema(
            {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": " 01.04.2026 19:08 ",
                "store": "REWE-Markt GmbH",
            }
        )

        self.assertEqual(normalized["purchase_date"], "01.04.2026 19:08")

    def test_normalize_receipt_schema_requires_explicit_or_embedded_retailer(self):
        with self.assertRaisesRegex(ValueError, "Receipt retailer fehlt"):
            normalize_receipt_schema(
                {
                    "id": "rewe-0605-8-01042026-1908-7714",
                    "purchase_date": "2026.04.01",
                }
            )


if __name__ == "__main__":
    unittest.main()

