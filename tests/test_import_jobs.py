import time


def test_start_import_job_tracks_progress(monkeypatch):
    from api.services import trigger_service
    from workflows.progress_display import ProgressState

    events = []

    def fake_run_lidl_initial(*, browser=None, cookies_file=None, country=None, output_dir=None, progress_listener=None):
        if progress_listener is not None:
            progress_listener(ProgressState(current=0, total=1, added=0, skipped=0, errors=0, items=0, current_receipt="-"))
            progress_listener(ProgressState(current=1, total=1, added=1, skipped=0, errors=0, items=3, current_receipt="r1"))
        events.append((browser, cookies_file, country, output_dir))
        return True

    monkeypatch.setattr(trigger_service, "run_lidl_initial", fake_run_lidl_initial)

    job_id = trigger_service.start_import_job("lidl")
    assert isinstance(job_id, str)

    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    assert state.status == "success"
    assert state.progress.current == 1
    assert state.progress.total == 1
    assert state.progress.current_receipt == "r1"
    assert events == [(None, None, None, None)]


def test_start_import_job_tracks_rewe_progress(monkeypatch):
    from api.services import trigger_service
    from workflows.progress_display import ProgressState

    def fake_run_rewe_initial(*, customer_id=None, browser=None, cookies_file=None, output_dir=None, progress_listener=None):
        if progress_listener is not None:
            progress_listener(ProgressState(current=0, total=2, added=0, skipped=0, errors=0, items=0, current_receipt="-"))
            progress_listener(ProgressState(current=2, total=2, added=2, skipped=0, errors=0, items=8, current_receipt="receipt-2"))
        return True

    monkeypatch.setattr(trigger_service, "run_rewe_initial", fake_run_rewe_initial)

    job_id = trigger_service.start_import_job("rewe")
    assert isinstance(job_id, str)

    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    assert state.status == "success"
    assert state.progress.current == 2
    assert state.progress.current_receipt == "receipt-2"


def test_get_import_job_returns_none_for_missing_job():
    from api.services import trigger_service

    assert trigger_service.get_import_job("missing") is None
