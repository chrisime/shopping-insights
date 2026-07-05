from shared.receipt_dto import AddressDTO, ReceiptDTO
from storage.sqlite_entity_builders import build_store_entity


def _build_receipt_dto(*, retailer: str, store: str, market: str | None, city: str) -> ReceiptDTO:
    return ReceiptDTO(
        id="r-1",
        retailer=retailer,
        purchase_date="2026-01-01",
        store=store,
        address=AddressDTO(street="Fronmuellerstr.", street_no="12", zip="90763", city=city),
        market=market,
        register_id=None,
        cashier=None,
        bon_number=None,
        total_price=1.0,
        discount=0.0,
        saved_deposit=0.0,
        currency="EUR",
        source_file=None,
        payload_hash="h",
    )


def test_build_store_entity_uses_market_as_primary_identity_hash_when_present():
    first = _build_receipt_dto(retailer="lidl", store="Lidl", market="4426", city="Fuerth-Suedstadt")
    second = _build_receipt_dto(retailer="lidl", store="Lidl", market="4426", city="Fuerth")

    first_store = build_store_entity(first)
    second_store = build_store_entity(second)

    assert first_store.hash == second_store.hash


def test_build_store_entity_keeps_store_and_city_as_provided():
    dto = _build_receipt_dto(retailer="lidl", store="Lidl", market="4426", city="Fuerth-Suedstadt")

    store = build_store_entity(dto)

    assert store.name == "Lidl"
    assert store.city == "Fuerth-Suedstadt"


def test_build_store_entity_keeps_official_hyphenated_city_names():
    dto = _build_receipt_dto(retailer="lidl", store="Lidl", market="6791", city="Garmisch-Partenkirchen")

    store = build_store_entity(dto)

    assert store.name == "Lidl"
    assert store.city == "Garmisch-Partenkirchen"


