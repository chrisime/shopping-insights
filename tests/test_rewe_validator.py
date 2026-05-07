import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from parsing.rewe_validator import (
    ReweReceiptValidationError,
    ReweValidationIssue,
    validate_rewe_receipt_data,
)
from shared.receipt_schema import normalize_receipt_schema
from workflows.rewe_workflow import parse_rewe_receipt_pdf_with_result


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
            "payment_methods": [{"method": "VISA", "amount": 1.0}],
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
            "payment_methods": [{"method": "VISA", "amount": 1.0}],
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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

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
                parse_result = parse_rewe_receipt_pdf_with_result(pdf_path)

        self.assertIsNone(parse_result.receipt_data)
        self.assertIn("Validatorfehler:", parse_result.skip_reason)
        self.assertIn("payment_methods: fehlen trotz positivem Gesamtbetrag", parse_result.skip_reason)

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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["total_price"], 5.97)
        self.assertEqual(receipt["total_price_no_saving"], 10.97)
        self.assertEqual(receipt["rewe_bonus_amount_saved"], 5.0)
        self.assertEqual(
            receipt["payment_methods"],
            [
                {"method": "Bonus-Guthaben", "amount": 5.0},
                {"method": "VISA", "amount": 5.97},
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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

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
                receipt = parse_rewe_receipt_pdf_with_result(pdf_path).receipt_data

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["rewe_bonus_amount"], 0.0)
        self.assertEqual(receipt["rewe_bonus_amount_saved"], 0.0)
        self.assertEqual(receipt["rewe_bonus_total_amount"], 15.93)

    def test_normalize_receipt_schema_defaults_rewe_bonus_fields_to_zero_and_converts_strings(self):
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

        self.assertEqual(normalized["rewe_bonus_amount"], 0.0)
        self.assertEqual(normalized["rewe_bonus_amount_saved"], 0.0)
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
        self.assertEqual(normalized["payment_methods"][0]["amount"], 1.0)
        self.assertEqual(normalized["items"][0]["price"], 22.95)
        self.assertEqual(normalized["items"][0]["quantity"], 1)
        self.assertEqual(normalized["items"][1]["quantity"], 0.696)


if __name__ == "__main__":
    unittest.main()

