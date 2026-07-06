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
