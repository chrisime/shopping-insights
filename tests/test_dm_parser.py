import unittest
from typing import Any
from unittest.mock import Mock

from parsing.dm_ebons_parser import enrich_dm_item_names, parse_dm_ebon
from parsing.dm_validator import (
    DmReceiptValidationError,
    validate_dm_receipt_data,
)


SAMPLE_EBON = {
    "id": "c51ccff9-13e9-47a0-a4f7-2d0c7dd03e91_2026",
    "date": "2026-01-07",
    "currency": "EUR",
    "totalAmount": 5.28,
    "followUpOrder": False,
    "address": {
        "name": "dm-drogerie markt",
        "street": "Rudolf-Breitscheid-Straße 14",
        "streetAdditional": None,
        "zip": "90762",
        "city": "Fürth",
    },
    "time": "14:54:27",
    "cashRegisterId": 4,
    "discount": 1.32,
    "totalPaybackPoints": 2,
    "hasDownloadableReceipt": True,
    "bonItems": [
        {"dan": "1446511", "description": ""},
        {"dan": "1446464", "description": "Drogerieartikel"},
    ],
}


class ParseDmEbonTests(unittest.TestCase):
    def _parse(self, data: dict) -> dict[str, Any]:
        return dict(parse_dm_ebon(data))

    def test_parses_happy_path(self):
        receipt = self._parse(SAMPLE_EBON)
        self.assertEqual(receipt["retailer"], "dm")
        self.assertEqual(receipt["id"], SAMPLE_EBON["id"])
        self.assertEqual(receipt["purchase_date"], "2026-01-07")
        self.assertEqual(receipt["total_price"], 5.28)
        self.assertEqual(receipt["discount"], 1.32)
        self.assertEqual(receipt["register"], "4")
        self.assertEqual(receipt["dm_payback_points"], 2)
        self.assertEqual(receipt["store"], "dm-drogerie markt")

    def test_parses_address_with_split_street_number(self):
        receipt = self._parse(SAMPLE_EBON)
        self.assertEqual(receipt["address"]["street"], "Rudolf-Breitscheid-Straße")
        self.assertEqual(receipt["address"]["street_no"], "14")
        self.assertEqual(receipt["address"]["zip"], "90762")
        self.assertEqual(receipt["address"]["city"], "Fürth")

    def test_parses_items_with_dan(self):
        receipt = self._parse(SAMPLE_EBON)
        self.assertEqual(len(receipt["items"]), 2)
        self.assertEqual(receipt["items"][0]["dan"], "1446511")
        self.assertEqual(receipt["items"][0]["name"], "")
        self.assertEqual(receipt["items"][1]["name"], "Drogerieartikel")

    def test_raises_when_id_missing(self):
        broken = dict(SAMPLE_EBON)
        broken.pop("id")
        with self.assertRaises(ValueError):
            parse_dm_ebon(broken)

    def test_raises_when_date_missing(self):
        broken = dict(SAMPLE_EBON)
        broken.pop("date")
        with self.assertRaises(ValueError):
            parse_dm_ebon(broken)

    def test_empty_bon_items_produce_no_items(self):
        empty = dict(SAMPLE_EBON)
        empty["bonItems"] = []
        receipt = self._parse(empty)
        self.assertEqual(receipt["items"], [])

    def test_uses_pdf_items_when_present(self):
        with_pdf = dict(SAMPLE_EBON)
        with_pdf["pdfItems"] = [
            {"name": "dmBio Roggen Vollkornmehl1000g", "price": 1.35, "quantity": 1, "unit": "stk"},
            {"name": "dmBio Buchweizenmehl 5", "price": 1.75, "quantity": 3, "unit": "stk"},
        ]
        receipt = self._parse(with_pdf)
        self.assertEqual(len(receipt["items"]), 2)
        self.assertEqual(receipt["items"][0]["name"], "dmBio Roggen Vollkornmehl1000g")
        self.assertEqual(receipt["items"][0]["price"], 1.35)
        self.assertEqual(receipt["items"][1]["name"], "dmBio Buchweizenmehl 5")
        self.assertEqual(receipt["items"][1]["quantity"], 3)
        self.assertEqual(receipt["items"][1]["price"], 1.75)

    def test_merges_dan_from_bon_items_by_position(self):
        with_pdf = dict(SAMPLE_EBON)
        with_pdf["pdfItems"] = [
            {"name": "Produkt A", "price": 1.0, "quantity": 1, "unit": "stk"},
        ]
        receipt = self._parse(with_pdf)
        self.assertEqual(len(receipt["items"]), 1)
        self.assertEqual(receipt["items"][0]["dan"], "1446511")


class EnrichDmItemNamesTests(unittest.TestCase):
    def test_keeps_existing_names(self):
        items = [{"dan": "1446511", "name": "Vorhanden", "price": None}]
        enrich_dm_item_names(items, session=None)
        self.assertEqual(items[0]["name"], "Vorhanden")

    def test_falls_back_when_gateway_unavailable(self):
        session = Mock()
        session.get.return_value.status_code = 404
        items = [{"dan": "1446511", "name": "", "price": None}]
        enrich_dm_item_names(items, session=session)
        self.assertEqual(items[0]["name"], "")

    def test_resolves_name_from_gateway(self):
        session = Mock()
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"name": "dm Produkt"}
        session.get.return_value = response
        items = [{"dan": "1446511", "name": "", "price": None}]
        enrich_dm_item_names(items, session=session)
        self.assertEqual(items[0]["name"], "dm Produkt")


class ValidateDmReceiptTests(unittest.TestCase):
    def test_valid_receipt_passes(self):
        validate_dm_receipt_data(parse_dm_ebon(SAMPLE_EBON))

    def test_rejects_wrong_retailer(self):
        receipt = parse_dm_ebon(SAMPLE_EBON)
        receipt["retailer"] = "rewe"
        with self.assertRaises(DmReceiptValidationError):
            validate_dm_receipt_data(receipt)

    def test_rejects_bad_id_format(self):
        receipt = parse_dm_ebon(SAMPLE_EBON)
        receipt["id"] = "not-a-dm-id"
        with self.assertRaises(DmReceiptValidationError):
            validate_dm_receipt_data(receipt)

    def test_rejects_missing_items(self):
        receipt = parse_dm_ebon(SAMPLE_EBON)
        receipt["items"] = []
        with self.assertRaises(DmReceiptValidationError):
            validate_dm_receipt_data(receipt)

    def test_rejects_missing_total(self):
        receipt = parse_dm_ebon(SAMPLE_EBON)
        receipt["total_price"] = None
        with self.assertRaises(DmReceiptValidationError):
            validate_dm_receipt_data(receipt)

    def test_rejects_bad_purchase_date(self):
        receipt = parse_dm_ebon(SAMPLE_EBON)
        receipt["purchase_date"] = "07.01.2026"
        with self.assertRaises(DmReceiptValidationError):
            validate_dm_receipt_data(receipt)


if __name__ == "__main__":
    unittest.main()