def test_receipts_list_is_paginated(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import receipt_service

    receipts = [
        {"id": "r1", "purchase_date": "2024-01-01", "total_price": 10.0},
        {"id": "r2", "purchase_date": "2024-01-02", "total_price": 20.0},
        {"id": "r3", "purchase_date": "2024-01-03", "total_price": 30.0},
    ]

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            return receipts

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts", params={"page": 2, "page_size": 2})

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {"id": "r3", "purchase_date": "2024-01-03", "total_price": 30.0}
        ],
        "meta": {"total": 3, "page_total": 2, "page": 2, "page_size": 2},
    }


def test_receipt_detail_returns_full_record(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import receipt_service

    receipts = [
        {
            "id": "r1",
            "purchase_date": "2024-01-01",
            "store": "Store A",
            "payment_methods": [{"method": "card", "amount": 10.0}],
            "items": [{"name": "Apfel", "quantity": 1, "unit": "pc", "price": 1.0}],
        }
    ]

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            return receipts

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/r1")

    assert response.status_code == 200
    assert response.json() == {"data": receipts[0]}


def test_receipt_items_returns_item_list(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import receipt_service

    receipts = [
        {
            "id": "r1",
            "items": [{"name": "Apfel", "quantity": 1, "unit": "pc", "price": 1.0}],
            "payment_methods": [{"method": "card", "amount": 1.0}],
        }
    ]

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            return receipts

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/r1/items")

    assert response.status_code == 200
    assert response.json() == {"data": receipts[0]["items"]}


def test_receipt_payments_returns_payment_list(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import receipt_service

    receipts = [
        {
            "id": "r1",
            "items": [{"name": "Apfel", "quantity": 1, "unit": "pc", "price": 1.0}],
            "payment_methods": [{"method": "card", "amount": 1.0}],
        }
    ]

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            return receipts

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/r1/payments")

    assert response.status_code == 200
    assert response.json() == {"data": receipts[0]["payment_methods"]}


def test_receipts_by_item_returns_matching_receipts(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import receipt_service

    class FakeStore:
        @staticmethod
        def list_receipts_by_item(name, retailer=None, start_date=None, end_date=None):
            return [
                {
                    "id": "r1",
                    "retailer": "lidl",
                    "purchase_date": "2024-01-15",
                    "store": "Lidl München",
                    "items": [
                        {"name": "Apfel", "quantity": 1, "unit": "kg", "price": 2.99, "matched": True},
                        {"name": "Brot", "quantity": 1, "unit": "pc", "price": 1.49},
                    ],
                    "payment_methods": [],
                }
            ]

    monkeypatch.setattr(receipt_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/receipts/by-item", params={"name": "Apfel"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "r1"
    assert data[0]["items"][0]["matched"] is True
