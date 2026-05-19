import unittest

from shared.receipt_hashes import (
    build_lidl_source_hash_payload,
    calculate_lidl_source_hash,
    calculate_receipt_payload_hash,
)


class ReceiptHashesTests(unittest.TestCase):
    def test_build_lidl_source_hash_payload_keeps_only_relevant_fields(self):
        payload = build_lidl_source_hash_payload(
            {
                "id": "receipt-1",
                "date": "28.08.2024",
                "isHtml": True,
                "totalAmount": 19.23,
                "page": 4,
                "uiBadge": "neu",
                "store": {
                    "id": "store-1",
                    "name": "Lidl Fürth",
                    "openingHours": "08:00-20:00",
                },
            }
        )

        self.assertEqual(
            payload,
            {
                "id": "receipt-1",
                "date": "28.08.2024",
                "isHtml": True,
                "totalAmount": 19.23,
                "store": {
                    "id": "store-1",
                    "name": "Lidl Fürth",
                },
            },
        )

    def test_calculate_lidl_source_hash_ignores_irrelevant_fields(self):
        first_hash = calculate_lidl_source_hash(
            {
                "id": "receipt-1",
                "date": "28.08.2024",
                "isHtml": True,
                "totalAmount": 19.23,
                "page": 1,
                "store": {"id": "store-1", "name": "Lidl Fürth"},
            }
        )
        second_hash = calculate_lidl_source_hash(
            {
                "id": "receipt-1",
                "date": "28.08.2024",
                "isHtml": True,
                "totalAmount": 19.23,
                "page": 99,
                "store": {"id": "store-1", "name": "Lidl Fürth", "openingHours": "08:00-20:00"},
            }
        )

        self.assertEqual(first_hash, second_hash)

    def test_calculate_lidl_source_hash_changes_for_relevant_fields(self):
        first_hash = calculate_lidl_source_hash(
            {
                "id": "receipt-1",
                "date": "28.08.2024",
                "isHtml": True,
                "totalAmount": 19.23,
                "store": {"id": "store-1", "name": "Lidl Fürth"},
            }
        )
        second_hash = calculate_lidl_source_hash(
            {
                "id": "receipt-1",
                "date": "28.08.2024",
                "isHtml": True,
                "totalAmount": 20.23,
                "store": {"id": "store-1", "name": "Lidl Fürth"},
            }
        )

        self.assertNotEqual(first_hash, second_hash)

    def test_calculate_receipt_payload_hash_ignores_hash_metadata_fields(self):
        first_hash = calculate_receipt_payload_hash(
            {
                "id": "receipt-1",
                "retailer": "lidl",
                "total_price": 19.23,
                "source_hash": "source-a",
                "payload_hash": "payload-a",
            }
        )
        second_hash = calculate_receipt_payload_hash(
            {
                "id": "receipt-1",
                "retailer": "lidl",
                "total_price": 19.23,
                "source_hash": "source-b",
                "payload_hash": "payload-b",
            }
        )

        self.assertEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()

