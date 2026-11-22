import unittest
from typing import Any

from parsing.rossmann_receipt_parser import parse_rossmann_receipt
from parsing.rossmann_validator import (
    RossmannReceiptValidationError,
    validate_rossmann_receipt_data,
)


SAMPLE_RECEIPT = {
    "id": "7ca5482b-73ab-4907-89fd-afc6214a14b6",
    "head": {
        "date": "2026-09-01T11:28:02.5247449+00:00",
        "externalReceiptId": "ext-1",
        "seller": {
            "name": "Rossmann Dresden",
            "vatId": "DE123456789",
            "address": {
                "street": "Hauptstrasse 1",
                "postalCode": "01067",
                "city": "Dresden",
                "countryCode": "DEU",
            },
        },
    },
    "data": {
        "currency": "EUR",
        "fullAmountInclVat": 10.0,
        "paymentMethods": [],
        "lines": [
            {
                "type": "Default",
                "sequenceNumber": 1,
                "text": "dmBio Hafermehl 500g",
                "fullAmountInclVat": 2.65,
                "item": {
                    "number": "4012",
                    "quantity": 2,
                    "quantityMeasure": "Count",
                    "pricePerUnit": 1.325,
                },
                "discounts": [],
                "isReturn": False,
            },
            {
                "type": "Text",
                "sequenceNumber": 2,
                "text": "------",
            },
            {
                "type": "Discount",
                "sequenceNumber": 3,
                "text": "Coupon 10%",
                "fullAmountInclVat": -1.0,
            },
        ],
    },
    "misc": None,
}


def _parse(data: dict) -> dict[str, Any]:
    return dict(parse_rossmann_receipt(data))


class ParseRossmannReceiptTests(unittest.TestCase):
    def test_preserves_undiscounted_unit_price(self):
        data = {
            **SAMPLE_RECEIPT,
            "data": {
                **SAMPLE_RECEIPT["data"],
                "lines": [
                    {"text": "A", "item": {"quantity": 2, "pricePerUnit": 1.35, "pricePerUnitBeforeDiscounts": 2.99}},
                    {"text": "B", "item": {"quantity": 2, "pricePerUnit": 1.35},
                     "fullAmountInclVatBeforeDiscounts": 5.98},
                ],
            },
        }
        assert [item["price"] for item in _parse(data)["items"]] == [2.99, 2.99]

    def test_parses_happy_path(self):
        receipt = _parse(SAMPLE_RECEIPT)
        self.assertEqual(receipt["retailer"], "rossmann")
        self.assertEqual(receipt["id"], SAMPLE_RECEIPT["id"])
        self.assertEqual(receipt["purchase_date"], "2026-09-01")
        self.assertEqual(receipt["store"], "Rossmann Dresden")
        self.assertEqual(receipt["total_price"], 10.0)
        self.assertEqual(receipt["currency"], "EUR")

    def test_parses_address(self):
        receipt = _parse(SAMPLE_RECEIPT)
        self.assertEqual(receipt["address"]["street"], "Hauptstrasse 1")
        self.assertEqual(receipt["address"]["zip"], "01067")
        self.assertEqual(receipt["address"]["city"], "Dresden")

    def test_uses_difference_between_receipt_totals_without_counting_item_discounts_again(self):
        data = {
            **SAMPLE_RECEIPT,
            "data": {
                **SAMPLE_RECEIPT["data"],
                "fullAmountInclVat": 10.03,
                "fullAmountInclVatBeforeDiscounts": 14.94,
                "lines": [{"type": "Default", "discounts": [{"fullAmountInclVat": 4.91}]}],
            },
        }
        self.assertEqual(_parse(data)["discount"], 4.91)

    def test_uses_item_discounts_when_the_original_total_is_missing(self):
        data = {
            **SAMPLE_RECEIPT,
            "data": {
                **SAMPLE_RECEIPT["data"],
                "lines": [{"type": "Default", "discounts": [{"fullAmountInclVat": 0.3}, {"fullAmountInclVat": 0.07}]}],
            },
        }
        self.assertEqual(_parse(data)["discount"], 0.37)

    def test_uses_separate_discount_line_when_no_other_discount_amount_is_available(self):
        receipt = _parse(SAMPLE_RECEIPT)
        self.assertEqual(receipt["discount"], 1.0)
        self.assertEqual(receipt["rossmann_coupon_discount"], 1.0)
        self.assertIsNone(receipt["rossmann_app_coupon_discount"])

    def test_handles_unmatched_coupon_amounts_without_guessing_their_origin(self):
        data = {
            **SAMPLE_RECEIPT,
            "data": {
                **SAMPLE_RECEIPT["data"],
                "fullAmountInclVatBeforeDiscounts": 11.5,
                "discounts": [{"id": "unlinked", "name": "Coupon Angebot", "value": 20}],
                "lines": [{"type": "Default", "discounts": [{"discountId": "missing", "fullAmountInclVat": 1.5}]}],
            },
        }
        receipt = _parse(data)
        self.assertEqual(receipt["discount"], 1.5)
        self.assertIsNone(receipt["rossmann_coupon_discount"])
        self.assertIsNone(receipt["rossmann_app_coupon_discount"])

    def test_only_default_lines_imported(self):
        receipt = _parse(SAMPLE_RECEIPT)
        self.assertEqual(len(receipt["items"]), 1)
        item = receipt["items"][0]
        self.assertEqual(item["name"], "dmBio Hafermehl 500g")
        self.assertEqual(item["quantity"], 2)
        self.assertEqual(item["price"], 1.325)
        self.assertEqual(item["unit"], "stk")

    def test_raises_when_id_missing(self):
        broken = dict(SAMPLE_RECEIPT)
        broken["id"] = ""
        with self.assertRaises(ValueError):
            parse_rossmann_receipt(broken)


class ValidateRossmannReceiptTests(unittest.TestCase):
    def test_valid_passes(self):
        validate_rossmann_receipt_data(parse_rossmann_receipt(SAMPLE_RECEIPT))

    def test_rejects_wrong_retailer(self):
        receipt = parse_rossmann_receipt(SAMPLE_RECEIPT)
        receipt["retailer"] = "rewe"
        with self.assertRaises(RossmannReceiptValidationError):
            validate_rossmann_receipt_data(receipt)

    def test_rejects_bad_id(self):
        receipt = parse_rossmann_receipt(SAMPLE_RECEIPT)
        receipt["id"] = "not-a-uuid"
        with self.assertRaises(RossmannReceiptValidationError):
            validate_rossmann_receipt_data(receipt)

    def test_rejects_bad_date(self):
        receipt = parse_rossmann_receipt(SAMPLE_RECEIPT)
        receipt["purchase_date"] = "01.09.2026"
        with self.assertRaises(RossmannReceiptValidationError):
            validate_rossmann_receipt_data(receipt)


if __name__ == "__main__":
    unittest.main()
