import unittest

from shared.receipt_dates import (
    is_normalized_purchase_date,
    normalize_purchase_date,
    normalize_purchase_date_from_receipt_id_token,
    parse_purchase_date,
)


class ReceiptDatesTests(unittest.TestCase):
    def test_parse_purchase_date_accepts_retailer_and_normalized_formats(self):
        self.assertEqual(parse_purchase_date("2026-04-01").date().isoformat(), "2026-04-01")
        self.assertEqual(parse_purchase_date("01.04.2026").date().isoformat(), "2026-04-01")

    def test_parse_purchase_date_rejects_legacy_historical_formats(self):
        self.assertIsNone(parse_purchase_date("01.04.2026 19:08"))
        self.assertIsNone(parse_purchase_date("2026.04.01"))
        self.assertIsNone(parse_purchase_date("2024-08-19T12:00:00"))

    def test_normalize_purchase_date_returns_iso_date(self):
        self.assertEqual(normalize_purchase_date("01.04.2026"), "2026-04-01")
        self.assertEqual(normalize_purchase_date("2024-08-19"), "2024-08-19")

    def test_normalize_purchase_date_returns_none_for_unsupported_legacy_formats(self):
        self.assertIsNone(normalize_purchase_date("01.04.2026 19:08"))
        self.assertIsNone(normalize_purchase_date("2024-08-19T12:00:00"))

    def test_is_normalized_purchase_date_accepts_only_valid_iso_dates(self):
        self.assertTrue(is_normalized_purchase_date("2026-04-01"))
        self.assertFalse(is_normalized_purchase_date("2026.04.01"))
        self.assertFalse(is_normalized_purchase_date("2026-13-40"))

    def test_normalize_purchase_date_from_receipt_id_token_converts_ddmmyyyy(self):
        self.assertEqual(normalize_purchase_date_from_receipt_id_token("01042026"), "2026-04-01")
        self.assertIsNone(normalize_purchase_date_from_receipt_id_token("2026-04-01"))


if __name__ == "__main__":
    unittest.main()

