import unittest

from shared.receipt_hashes import (
    calculate_receipt_payload_hash,
)


class ReceiptHashesTests(unittest.TestCase):

    def test_calculate_receipt_payload_hash_ignores_payload_hash_metadata_field(self):
        first_hash = calculate_receipt_payload_hash(
            {
                "id": "receipt-1",
                "retailer": "lidl",
                "total_price": 19.23,
                "payload_hash": "payload-a",
            }
        )
        second_hash = calculate_receipt_payload_hash(
            {
                "id": "receipt-1",
                "retailer": "lidl",
                "total_price": 19.23,
                "payload_hash": "payload-b",
            }
        )

        self.assertEqual(first_hash, second_hash)


if __name__ == "__main__":
    unittest.main()

