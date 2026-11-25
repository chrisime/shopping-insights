from datetime import date, timedelta

import pytest


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
            return [{"id": "r1", "total_price": 10.0}] if retailer == "lidl" else []

    monkeypatch.setattr(export_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/exports/receipts")

    assert response.status_code == 200
    assert response.json() == {"data": [{"id": "r1", "total_price": 10.0}]}


def test_receipt_export_without_retailer_merges_all_retailers(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import export_service

    calls = []

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            calls.append(retailer)
            if retailer == "lidl":
                return [{"id": "l1", "purchase_date": "2024-02-01", "total_price": 20.0}]
            if retailer == "rewe":
                return [{"id": "r1", "purchase_date": "2024-01-01", "total_price": 10.0}]
            return []

    monkeypatch.setattr(export_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get("/exports/receipts")

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {"id": "l1", "purchase_date": "2024-02-01", "total_price": 20.0},
            {"id": "r1", "purchase_date": "2024-01-01", "total_price": 10.0},
        ]
    }
    assert calls == ["lidl", "rewe", "dm", "rossmann"]


def test_receipt_export_filters_by_retailer_and_date_range(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import export_service

    class FakeStore:
        @staticmethod
        def list_receipts(retailer):
            assert retailer == "lidl"
            return [
                {"id": "r1", "purchase_date": "2024-01-01", "total_price": 10.0},
                {"id": "r2", "purchase_date": "2024-02-01", "total_price": 20.0},
            ]

    monkeypatch.setattr(export_service, "SqliteReceiptStore", FakeStore)

    response = TestClient(app).get(
        "/exports/receipts",
        params={"retailer": "lidl", "start_date": "2024-01-01", "end_date": "2024-01-31"},
    )

    assert response.status_code == 200
    assert response.json() == {"data": [{"id": "r1", "purchase_date": "2024-01-01", "total_price": 10.0}]}


def test_kpi_export_returns_summary_and_bonus(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import export_service

    monkeypatch.setattr(export_service, "export_kpis", lambda retailer=None: {"summary": {"total_spent": 10.0}, "bonus": {"lidlplus_discount": 1.0}})

    response = TestClient(app).get("/exports/kpis")

    assert response.status_code == 200
    assert response.json() == {"data": {"summary": {"total_spent": 10.0}, "bonus": {"lidlplus_discount": 1.0}}}


@pytest.mark.parametrize("retailer", ["lidl", "rewe", "dm", "rossmann"])
def test_fetch_trigger_passes_purchase_cutoff(monkeypatch, retailer):
    from fastapi.testclient import TestClient

    from api.main import app
    from api.services import trigger_service

    from auth.rossmann_auth import RossmannAccount

    called = []
    credentials = {}
    account_args = {}
    if retailer == "rossmann":
        credentials = {"json": {"email": " user@example.com ", "password": "example-password"}}
        account_args = {"account_id": "account-id", "account_hash": "account-hash"}

        def fake_authenticate(email, password):
            assert (email, password) == ("user@example.com", "example-password")
            return RossmannAccount(**account_args)

        monkeypatch.setattr(trigger_service, "authenticate_rossmann_account", fake_authenticate)

    def fake_run_initial(*, purchased_since, **kwargs):
        if retailer == "rossmann":
            assert kwargs == account_args
        called.append(purchased_since)
        return True

    monkeypatch.setattr(trigger_service, f"run_{retailer}_initial", fake_run_initial)

    client = TestClient(app)
    response = client.post(f"/triggers/fetch/{retailer}", params={"days_back": 7}, **credentials)

    assert response.status_code == 200
    assert response.json() == {"data": {"retailer": retailer, "started": True, "days_back": 7}}
    assert called == [date.today() - timedelta(days=7)]
    assert client.post(f"/triggers/fetch/{retailer}", params={"days_back": -1}, **credentials).status_code == 422
    assert len(called) == 1


@pytest.mark.parametrize("endpoint", ["/items", "/receipts"])
@pytest.mark.parametrize("parameter", ["page", "page_size"])
def test_list_endpoints_reject_zero_pagination(endpoint, parameter):
    from fastapi.testclient import TestClient

    from api.main import app

    response = TestClient(app).get(endpoint, params={parameter: 0})

    assert response.status_code == 422
    assert response.json()["error_code"] == 4001


def test_lidl_cutoff_excludes_old_detail_requests_without_skipping_next_page(monkeypatch):
    from client import lidl_client
    from shared.lidl_ticket_dto import LidlTicketsPageDTO

    cutoff = date(2026, 11, 18)
    pages = {
        1: {"totalCount": 2, "items": [{"ticket": {"id": "old", "isHtml": True, "date": "2026-11-17"}}]},
        2: {"totalCount": 2, "items": [{"ticket": {"id": "keep", "isHtml": True, "date": "2026-11-18"}}]},
    }
    monkeypatch.setattr(
        lidl_client, "get_tickets_page", lambda session, page: LidlTicketsPageDTO.from_api_response(pages[page], page)
    )

    assert lidl_client.collect_lidl_receipt_ids(object(), purchased_since=cutoff) == (["keep"], 2)


def test_dm_cutoff_excludes_older_purchases_and_stops_pagination(monkeypatch):
    from client import dm_client

    cutoff = date(2026, 11, 18)
    matching = {"id": "keep", "dateTimePlaced": "2026-11-18T00:00:00+01:00"}
    older = {"id": "old", "dateTimePlaced": "2026-11-17T22:05:00Z"}
    calls = []

    def fetch_history(session, *, until_date_time_placed, token_refresher):
        calls.append(until_date_time_placed)
        return {"purchaseHistoryItems": [matching, older], "hasMoreElements": True}

    monkeypatch.setattr(dm_client, "fetch_purchase_history", fetch_history)
    assert dm_client.collect_dm_purchases(object(), purchased_since=cutoff) == [matching]
    assert calls == [None]
