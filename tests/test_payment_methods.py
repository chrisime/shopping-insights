import unittest

from shared.payment_methods import normalize_payment_method_entry


class PaymentMethodsTests(unittest.TestCase):
    def test_normalize_payment_method_entry_assigns_rewe_network_to_unknown_inflationspraemie(self):
        normalized = normalize_payment_method_entry(
            {
                "method": "Inflationsprämie",
                "retailer": "rewe",
                "amount": "7,20",
            }
        )

        self.assertEqual(
            normalized,
            {
                "method": "Inflationsprämie",
                "network": "REWE",
                "amount": 7.2,
            },
        )

    def test_normalize_payment_method_entry_assigns_rewe_network_to_unknown_method_with_explicit_retailer(self):
        normalized = normalize_payment_method_entry(
            {
                "method": "Payback Pay",
                "retailer": "rewe",
                "amount": "7,20",
            }
        )

        self.assertEqual(
            normalized,
            {
                "method": "Payback Pay",
                "network": "REWE",
                "amount": 7.2,
            },
        )

    def test_normalize_payment_method_entry_uses_unknown_network_text_as_method_for_lidl(self):
        normalized = normalize_payment_method_entry(
            {
                "network": "Geldger├ñte",
                "retailer": "lidl",
                "amount": "3,50",
            }
        )

        self.assertEqual(
            normalized,
            {
                "method": "Geldger├ñte",
                "network": "LIDL",
                "amount": 3.5,
            },
        )

    def test_normalize_payment_method_entry_maps_bonus_guthaben_to_rewe_network(self):
        normalized = normalize_payment_method_entry(
            {
                "method": "Bonus-Guthaben",
                "amount": "5,00",
            }
        )

        self.assertEqual(
            normalized,
            {
                "method": "Bonus-Guthaben",
                "network": "REWE",
                "amount": 5.0,
            },
        )

    def test_normalize_payment_method_entry_keeps_card_networks_as_card_payments(self):
        normalized = normalize_payment_method_entry(
            {
                "method": "VISA",
                "retailer": "rewe",
                "amount": "5,00",
            }
        )

        self.assertEqual(
            normalized,
            {
                "method": "Karte",
                "network": "VISA",
                "amount": 5.0,
            },
        )


if __name__ == "__main__":
    unittest.main()

