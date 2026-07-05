def test_items_endpoint_flattens_receipt_items(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import item_service

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            return [
                {
                    "id": "r1",
                    "items": [
                        {"name": "Apfel", "quantity": 2, "unit": "pc", "price": 1.0},
                        {"name": "Banane", "quantity": 1, "unit": "pc", "price": 2.0},
                    ],
                }
            ]

    monkeypatch.setattr(item_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/items", params={"search": "ap"})

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {"receipt_id": "r1", "name": "Apfel", "quantity": 2, "unit": "pc", "price": 1.0}
        ],
        "meta": {"total": 1, "page_total": 1, "page": 1, "page_size": 50},
    }


def test_receipt_export_reuses_receipt_data(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import export_service

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            return [{"id": "r1", "total_price": 10.0}]

    monkeypatch.setattr(export_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/exports/receipts")

    assert response.status_code == 200
    assert response.json() == {"data": [{"id": "r1", "total_price": 10.0}]}


def test_kpi_export_returns_summary_and_bonus(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import export_service

    monkeypatch.setattr(export_service, "export_kpis", lambda retailer=None: {"summary": {"total_spent": 10.0}, "bonus": {"lidlplus_discount": 1.0}})

    response = TestClient(app).get("/exports/kpis")

    assert response.status_code == 200
    assert response.json() == {"data": {"summary": {"total_spent": 10.0}, "bonus": {"lidlplus_discount": 1.0}}}


def test_lidl_fetch_trigger_calls_workflow(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import trigger_service

    called = []

    def fake_run_lidl_initial(*, browser=None, cookies_file=None, country=None, output_dir=None):
        called.append((browser, cookies_file, country, output_dir))
        return True

    monkeypatch.setattr(trigger_service, "run_lidl_initial", fake_run_lidl_initial)

    response = TestClient(app).post("/triggers/fetch/lidl", params={"days_back": 7})

    assert response.status_code == 200
    assert response.json() == {"data": {"retailer": "lidl", "started": True, "days_back": 7}}
    assert called == [(None, None, None, None)]
