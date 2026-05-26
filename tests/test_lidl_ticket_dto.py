"""Tests for api.lidl_ticket_dto – LidlTicketDTO and LidlStoreDTO."""

from shared.lidl_ticket_dto import LidlTicketDTO, LidlStoreDTO, _split_address_line


class TestLidlTicketDTO:
    def test_from_api_response_extracts_all_fields(self):
        raw = {
            "id": "23004426832026051669963",
            "date": "2026-05-16T15:46:35",
            "htmlPrintedReceipt": "<html>...</html>",
            "store": {
                "id": None,
                "name": "Fürth-Südstadt",
                "address": "Fronmüllerstr. 12",
                "postalCode": "90763",
                "locality": "Fürth",
            },
        }

        ticket = LidlTicketDTO.from_api_response(raw)

        assert ticket.id == "23004426832026051669963"
        assert ticket.date == "2026-05-16T15:46:35"
        assert ticket.html_receipt == "<html>...</html>"
        assert ticket.store.name == "Fürth-Südstadt"

    def test_from_api_response_uses_receipt_id_fallback(self):
        raw = {"date": "2026-05-16", "htmlPrintedReceipt": "<html/>"}

        ticket = LidlTicketDTO.from_api_response(raw, receipt_id="fallback-123")

        assert ticket.id == "fallback-123"

    def test_from_api_response_handles_string_store(self):
        raw = {
            "id": "123",
            "date": "2026-01-01",
            "htmlPrintedReceipt": "<html/>",
            "store": "My Store",
        }

        ticket = LidlTicketDTO.from_api_response(raw)

        assert ticket.store.name == "My Store"
        assert not ticket.store.has_address()

    def test_from_api_response_handles_missing_store(self):
        raw = {"id": "123", "date": "2026-01-01", "htmlPrintedReceipt": "<html/>"}

        ticket = LidlTicketDTO.from_api_response(raw)

        assert ticket.store.name == "Lidl"
        assert not ticket.store.has_address()

    def test_to_api_dict_roundtrip_preserves_store_name_and_city(self):
        raw = {
            "id": "23004426832026051669963",
            "date": "2026-05-16T15:46:35",
            "htmlPrintedReceipt": "<html>...</html>",
            "store": {
                "name": "Fürth-Südstadt",
                "street": "Fronmüllerstr.",
                "street_no": "12",
                "zip": "90763",
                "city": "Fürth",
            },
        }

        ticket = LidlTicketDTO.from_api_response(raw)
        serialized = ticket.to_api_dict()
        roundtripped = LidlTicketDTO.from_api_response(serialized)

        assert roundtripped.store.name == "Fürth-Südstadt"
        assert roundtripped.store.city == "Fürth"


class TestLidlStoreDTO:
    def test_address_split_from_combined_field(self):
        raw = {
            "id": "123",
            "date": "2026-01-01",
            "htmlPrintedReceipt": "",
            "store": {
                "name": "Fürth-Südstadt",
                "address": "Fronmüllerstr. 12",
                "postalCode": "90763",
                "locality": "Fürth",
            },
        }

        ticket = LidlTicketDTO.from_api_response(raw)
        store = ticket.store

        assert store.street == "Fronmüllerstr."
        assert store.street_no == "12"
        assert store.zip == "90763"
        assert store.city == "Fürth"

    def test_address_dict_conversion(self):
        store = LidlStoreDTO(
            name="Test",
            street="Hauptstr.",
            street_no="5",
            zip="12345",
            city="Berlin",
        )

        address_dict = store.to_address_dict()

        assert address_dict == {
            "street": "Hauptstr.",
            "street_no": "5",
            "zip": "12345",
            "city": "Berlin",
        }

    def test_has_address_true_when_any_field_set(self):
        store = LidlStoreDTO(name="X", street=None, street_no=None, zip="12345", city=None)
        assert store.has_address()

    def test_has_address_false_when_all_none(self):
        store = LidlStoreDTO(name="X", street=None, street_no=None, zip=None, city=None)
        assert not store.has_address()

    def test_legacy_store_keys(self):
        """Ensure old API key variants (streetName, zipCode, town, etc.) still work."""
        raw = {
            "id": "x",
            "date": "2026-01-01",
            "htmlPrintedReceipt": "",
            "store": {
                "name": "Alt-Store",
                "streetName": "Bahnhofstr.",
                "streetNo": "7a",
                "zipCode": "80331",
                "town": "München",
            },
        }

        ticket = LidlTicketDTO.from_api_response(raw)
        store = ticket.store

        assert store.street == "Bahnhofstr."
        assert store.street_no == "7a"
        assert store.zip == "80331"
        assert store.city == "München"


class TestSplitAddressLine:
    def test_splits_street_and_number(self):
        assert _split_address_line("Fronmüllerstr. 12") == ("Fronmüllerstr.", "12")

    def test_splits_with_letter_suffix(self):
        assert _split_address_line("Hauptstr. 5a") == ("Hauptstr.", "5a")

    def test_returns_none_for_no_number(self):
        street, no = _split_address_line("Am Marktplatz")
        assert street == "Am Marktplatz"
        assert no is None

    def test_returns_nones_for_empty(self):
        assert _split_address_line("") == (None, None)
        assert _split_address_line(None) == (None, None)

