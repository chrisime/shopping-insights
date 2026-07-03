import json
import tempfile
import unittest
from pathlib import Path

from parsing.receipt_schema import normalize_receipt_schema as parsing_normalize_receipt_schema
from receipt_schema import normalize_receipt_schema as root_normalize_receipt_schema
from shared.receipt_schema import normalize_receipt_schema
from storage.receipt_repository import sort_receipts_by_date, upsert_receipts


class ReceiptRepositoryTests(unittest.TestCase):
    def test_upsert_receipts_normalizes_and_updates_legacy_url_records(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "receipts.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "url": "rewe-0605-8-01042026-1908-7714",
                            "purchase_date": "01.04.2026 19:08",
                            "store": "REWE Markt GmbH",
                            "address": {
                                "street": " Kaiserstr. ",
                                "street_no": "22",
                                "zip": "90763",
                                "city": " Fürth ",
                            },
                            "total_price": "1,00",
                            "payment_methods": None,
                            "items": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            created_count, updated_count, total_count = upsert_receipts(
                [
                    {
                        "id": "rewe-0605-8-01042026-1908-7714",
                        "retailer": "rewe",
                        "purchase_date": "2026.04.01",
                        "store": "REWE Markt GmbH",
                        "address": {
                            "street": "Kaiserstr.",
                            "street_no": "22",
                            "zip": "90763",
                            "city": "Fürth",
                        },
                        "total_price": "1,00",
                        "payment_methods": [{"method": "VISA", "amount": "1,00"}],
                        "items": [{"name": "Banane", "price": "1,00", "quantity": "1", "unit": "stk"}],
                    }
                ],
                file_path=str(file_path),
                retailer="rewe",
            )

            self.assertEqual((created_count, updated_count, total_count), (0, 1, 1))

            saved_receipts = json.loads(file_path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved_receipts), 1)
            self.assertEqual(saved_receipts[0]["retailer"], "rewe")
            self.assertEqual(saved_receipts[0]["purchase_date"], "2026.04.01")
            self.assertEqual(saved_receipts[0]["address"]["zip"], 90763)
            self.assertEqual(saved_receipts[0]["payment_methods"][0]["amount"], 1.0)
            self.assertEqual(saved_receipts[0]["items"][0]["quantity"], 1)
            self.assertEqual(saved_receipts[0]["rewe_bonus_amount"], 0.0)
            self.assertEqual(saved_receipts[0]["rewe_bonus_amount_saved"], 0.0)

    def test_sort_receipts_by_date_orders_mixed_legacy_and_normalized_formats_descending(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "receipts.json"
            file_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "a",
                            "retailer": "lidl",
                            "purchase_date": "01.04.2026 10:15",
                        },
                        {
                            "id": "b",
                            "retailer": "rewe",
                            "purchase_date": "2026.05.02",
                        },
                        {
                            "id": "c",
                            "retailer": "lidl",
                            "purchase_date": "30.03.2026",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            count = sort_receipts_by_date(file_path=str(file_path), retailer="lidl")

            self.assertEqual(count, 3)
            saved_receipts = json.loads(file_path.read_text(encoding="utf-8"))
            self.assertEqual([receipt["id"] for receipt in saved_receipts], ["b", "a", "c"])

    def test_compatibility_wrappers_delegate_to_shared_receipt_schema(self):
        payload = {
            "id": "23004426420240828113520",
            "purchase_date": "2024.08.28",
            "address": {"zip": "90762"},
            "items": [{"name": "Tomaten", "price": "3,99", "quantity": "0,696", "unit": "kg"}],
        }

        normalized_shared = normalize_receipt_schema(payload, retailer="lidl")
        normalized_root = root_normalize_receipt_schema(payload, retailer="lidl")
        normalized_parsing = parsing_normalize_receipt_schema(payload, retailer="lidl")

        self.assertEqual(normalized_root, normalized_shared)
        self.assertEqual(normalized_parsing, normalized_shared)
        self.assertEqual(normalized_shared["address"]["zip"], 90762)
        self.assertEqual(normalized_shared["lidlplus_amount_saved"], 0.0)
        self.assertEqual(normalized_shared["items"][0]["quantity"], 0.696)


if __name__ == "__main__":
    unittest.main()

