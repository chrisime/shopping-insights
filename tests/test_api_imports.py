import json
from functools import partial

from fastapi.testclient import TestClient


def test_import_start_returns_job_id(monkeypatch):
    from api.main import app
    from api.services import import_job_service

    monkeypatch.setattr(import_job_service, "start_import_job", lambda retailer: "job-1")

    response = TestClient(app).post("/imports/start", json={"retailer": "lidl"})

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-1", "retailer": "lidl"}


def test_import_start_returns_conflict_when_job_running(monkeypatch):
    from api.main import app
    from api.services import import_job_service

    monkeypatch.setattr(import_job_service, "start_import_job", lambda retailer: (_ for _ in ()).throw(RuntimeError("Import job already running: job-1")))

    response = TestClient(app).post("/imports/start", json={"retailer": "rewe"})

    assert response.status_code == 409
    assert response.json() == {"detail": {"error_code": 4091, "detail": "Import bereits aktiv"}}


def test_import_events_streams_progress_and_success(monkeypatch):
    from api.main import app
    from api.services import import_job_service

    monkeypatch.setattr(
        import_job_service,
        "get_import_job",
        lambda job_id: object() if job_id == "job-1" else None,
    )
    monkeypatch.setattr(
        import_job_service,
        "iter_import_job_events",
        lambda job_id: iter(
            [
                {
                    "event": "progress",
                    "data": {
                        "job_id": job_id,
                        "retailer": "lidl",
                        "status": "running",
                        "progress": {
                            "current": 1,
                            "total": 2,
                            "added": 1,
                            "skipped": 0,
                            "errors": 0,
                            "items": 3,
                            "current_receipt": "r1",
                        },
                        "message": None,
                    },
                },
                {
                    "event": "success",
                    "data": {
                        "job_id": job_id,
                        "retailer": "lidl",
                        "status": "success",
                        "progress": {
                            "current": 2,
                            "total": 2,
                            "added": 2,
                            "skipped": 0,
                            "errors": 0,
                            "items": 6,
                            "current_receipt": "r2",
                        },
                        "message": None,
                    },
                },
            ]
        ),
    )

    response = TestClient(app).get("/imports/job-1/events")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: progress" in response.text
    assert "event: success" in response.text


def test_import_events_streams_structured_error(monkeypatch):
    from api.main import app
    from api.services import import_job_service

    monkeypatch.setattr(
        import_job_service,
        "get_import_job",
        lambda job_id: object() if job_id == "job-1" else None,
    )
    monkeypatch.setattr(
        import_job_service,
        "iter_import_job_events",
        lambda job_id: iter(
            [
                {
                    "event": "error",
                    "data": {
                        "job_id": job_id,
                        "retailer": "lidl",
                        "status": "error",
                        "progress": {
                            "current": 0,
                            "total": 1,
                            "added": 0,
                            "skipped": 0,
                            "errors": 1,
                            "items": 0,
                            "current_receipt": "-",
                        },
                        "error": {"error_code": 2102, "detail": "Nicht autorisiert (401)"},
                        "message": "Import fehlgeschlagen",
                    },
                }
            ]
        ),
    )

    response = TestClient(app).get("/imports/job-1/events")

    assert response.status_code == 200
    assert "event: error" in response.text
    assert '"error_code": 2102' in response.text
    assert "Nicht autorisiert (401)" in response.text


def test_import_start_surfaces_structured_backend_error(monkeypatch):
    from api.main import app
    from api.services import import_job_service

    monkeypatch.setattr(
        import_job_service,
        "start_import_job",
        lambda retailer: (_ for _ in ()).throw(RuntimeError("Import workflow returned False for retailer: lidl")),
    )

    response = TestClient(app).post("/imports/start", json={"retailer": "lidl"})

    assert response.status_code == 409
    assert response.json() == {"detail": {"error_code": 4091, "detail": "Import bereits aktiv"}}


def test_rossmann_import_adds_new_receipt_with_items_only_once(monkeypatch, tmp_path):
    from api.main import app
    from api.services import import_job_service, trigger_service
    from auth.rossmann_auth import RossmannAccount
    from config import storage_config
    from storage.sqlite_receipt_store import SqliteReceiptStore
    from workflows import rossmann_workflow

    first_id = "caa469d4-346d-461f-a768-16cb35e9459b"
    new_id = "d09097f3-7765-45b4-a0b0-0de38d93842e"
    listed_ids = [first_id]
    requested_details = []

    def authenticate(email, password):
        assert (email, password) == ("person@example.test", "test-password")
        return RossmannAccount("account", "hash")

    def fetch_detail(session, receipt_id, *, token_refresher):
        requested_details.append(receipt_id)
        day, name = ("01", "Shampoo") if receipt_id == first_id else ("02", "Zahnpasta")
        item = {"type": "Default", "text": name, "item": {"quantity": 2, "pricePerUnit": 2.25}}
        data = {"fullAmountInclVat": 4.50, "fullAmountInclVatBeforeDiscounts": 4.50, "lines": [item]}
        if receipt_id == new_id:
            data["fullAmountInclVatBeforeDiscounts"] = 6.00
            data["discounts"] = [
                {"id": "generic", "name": "10% COUPONAKTION", "value": 10},
                {"id": "app", "name": "App-Coupon Zahnpasta", "fullAmountInclVat": 0.6},
            ]
            item["discounts"] = [
                {"discountId": "generic", "fullAmountInclVat": 0.4},
                {"discountId": "app", "fullAmountInclVat": 0.6},
            ]
        return {
            "id": receipt_id,
            "head": {"date": f"2026-11-{day}T11:00:00Z", "seller": {"name": "Rossmann"}},
            "data": data,
        }

    monkeypatch.setattr(storage_config, "SQLITE_RECEIPTS_DB_FILE", str(tmp_path / "receipts.sqlite"))
    monkeypatch.setattr(import_job_service, "authenticate_rossmann_account", authenticate)
    monkeypatch.setattr(trigger_service, "run_rossmann_initial",
                        partial(rossmann_workflow.run_rossmann_initial, output_dir=str(tmp_path)))
    monkeypatch.setattr(rossmann_workflow, "build_anybill_api_session", lambda *args: object())
    monkeypatch.setattr(rossmann_workflow, "_test_rossmann_client_session", lambda *args: True)
    monkeypatch.setattr(rossmann_workflow, "collect_rossmann_receipts",
                        lambda *args, **kwargs: [{"id": receipt_id} for receipt_id in listed_ids])
    monkeypatch.setattr(rossmann_workflow, "fetch_receipt_detail", fetch_detail)
    monkeypatch.setattr(rossmann_workflow, "download_receipt_pdf", lambda *args, **kwargs: None)
    client = TestClient(app)

    def import_from_dashboard():
        response = client.post("/imports/start", json={
            "retailer": "rossmann",
            "rossmann_login": {"email": "person@example.test", "password": "test-password"},
        })
        assert response.status_code == 200
        stream = client.get(f"/imports/{response.json()['job_id']}/events")
        assert "event: success" in stream.text
        assert "test-password" not in stream.text
        return json.loads(stream.text.strip().splitlines()[-1].removeprefix("data: "))

    assert import_from_dashboard()["progress"]["added"] == 1
    listed_ids.insert(0, new_id)
    result = import_from_dashboard()
    assert result["progress"]["added"] == 1
    assert result["progress"]["items"] == 1
    repeat = import_from_dashboard()
    assert repeat["progress"]["added"] == repeat["progress"]["items"] == 0
    assert requested_details == [first_id, new_id]

    receipts = {receipt["id"]: receipt["items"] for receipt in SqliteReceiptStore.list_receipts("rossmann")}
    assert set(receipts) == {first_id, new_id}
    assert [item["name"] for item in receipts[first_id]] == ["Shampoo"]
    assert [item["name"] for item in receipts[new_id]] == ["Zahnpasta"]
    coupons = [
        {"name": "10% COUPONAKTION", "savings": 0.40},
        {"name": "App-Coupon Zahnpasta", "savings": 0.60},
    ]
    for endpoint, params in [
        ("by-item", {"name": "Zahnpasta"}),
        ("by-date", {"start_date": "2026-11-02", "end_date": "2026-11-02"}),
    ]:
        response = client.get(f"/receipts/{endpoint}", params={"retailer": "rossmann", **params})
        assert response.status_code == 200
        assert response.json()[0]["rossmann_coupons"] == coupons
    dashboard = client.get("/ui/dashboard", params={"retailer": "rossmann"})
    assert dashboard.status_code == 200
    metrics = next(section["items"][0] for section in dashboard.json()["sections"] if section["kind"] == "metrics")
    assert metrics["receipt_count"] == 2
    assert metrics["rossmann_discount_amount"] == metrics["total_savings"] == 1.50
    assert metrics["rossmann_discount_pct"] == 16.67
    assert metrics["spendings_without_discount"] == 10.50
    assert metrics["rossmann_coupon_discount_amount"] == 0.40
    assert metrics["rossmann_app_coupon_discount_amount"] == 0.60
    assert metrics["rossmann_basket_coupon_amount"] == 0.40
    assert metrics["rossmann_product_coupon_amount"] == 0.60
    assert metrics["rossmann_unclassified_coupon_amount"] == 0
    assert metrics["rossmann_other_discount_amount"] == 0.50

    date_filtered = client.get("/ui/dashboard", params={"retailer": "rossmann", "end_date": "2026-11-01"})
    metrics = next(section["items"][0] for section in date_filtered.json()["sections"] if section["kind"] == "metrics")
    assert metrics["rossmann_discount_amount"] == metrics["rossmann_discount_pct"] == 0
    assert "rossmann_app_coupon_discount_amount" not in metrics

    dashboard = client.get("/ui/dashboard")
    metrics = next(section["items"][0] for section in dashboard.json()["sections"] if section["kind"] == "metrics")
    assert metrics["rossmann_discount_amount"] == 1.50
    assert metrics["rossmann_app_coupon_discount_amount"] == 0.60
