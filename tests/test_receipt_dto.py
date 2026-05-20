import unittest

from shared.receipt_dto import receipt_dict_to_dto, receipt_dto_to_dict


class ReceiptDtoTests(unittest.TestCase):
    def test_receipt_dict_to_dto_maps_core_fields(self):
        receipt = receipt_dict_to_dto(
            {
                "id": "receipt-1",
                "retailer": "lidl",
                "purchase_date": "2026-05-09",
                "store": "LIDL",
                "address": {
                    "street": "Hauptstr.",
                    "street_no": "5",
                    "zip": "90762",
                    "city": "Fürth",
                },
                "payload_hash": "hash-1",
                "items": [{"name": "Banane", "quantity": 1, "unit": "stk", "price": 1.0}],
                "payment_methods": [{"method": "Karte", "network": "VISA", "amount": 1.0}],
            }
        )

        self.assertEqual(receipt.id, "receipt-1")
        self.assertEqual(receipt.retailer, "lidl")
        self.assertEqual(receipt.items[0].position, 1)
        self.assertEqual(receipt.payment_methods[0].position, 1)

    def test_receipt_dto_to_dict_preserves_register_field_name(self):
        receipt = receipt_dict_to_dto(
            {
                "id": "receipt-2",
                "retailer": "rewe",
                "purchase_date": "2026-05-09",
                "store": "REWE",
                "address": {"street": "A", "street_no": "1", "zip": "1", "city": "B"},
                "payload_hash": "hash-2",
                "register": "4",
            }
        )

        exported = receipt_dto_to_dict(receipt)
        self.assertEqual(exported["register"], "4")


if __name__ == "__main__":
    unittest.main()

