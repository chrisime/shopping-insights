import time
from threading import Event


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


def test_start_import_job_marks_false_return_as_error(monkeypatch):
    from api.services import trigger_service

    def fake_run_lidl_initial(*, browser=None, cookies_file=None, country=None, output_dir=None, progress_listener=None):
        return False

    monkeypatch.setattr(trigger_service, "run_lidl_initial", fake_run_lidl_initial)

    job_id = trigger_service.start_import_job("lidl")

    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    assert state.status == "error"
    assert "returned False" in (state.message or "")


def test_start_import_job_marks_none_return_as_error(monkeypatch):
    from api.services import trigger_service

    def fake_run_rewe_initial(*, customer_id=None, browser=None, cookies_file=None, output_dir=None, progress_listener=None):
        return None

    monkeypatch.setattr(trigger_service, "run_rewe_initial", fake_run_rewe_initial)

    job_id = trigger_service.start_import_job("rewe")

    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    assert state.status == "error"
    assert "returned False" in (state.message or "")


def test_start_import_job_rejects_second_running_job(monkeypatch):
    from api.services import trigger_service
    from workflows.progress_display import ProgressState

    release = Event()

    def fake_run_lidl_initial(*, browser=None, cookies_file=None, country=None, output_dir=None, progress_listener=None):
        if progress_listener is not None:
            progress_listener(ProgressState(current=0, total=1, added=0, skipped=0, errors=0, items=0, current_receipt="-"))
        release.wait(timeout=2)
        return True

    monkeypatch.setattr(trigger_service, "run_lidl_initial", fake_run_lidl_initial)

    job_id = trigger_service.start_import_job("lidl")
    deadline = time.time() + 2
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status == "running":
            break
        time.sleep(0.01)

    try:
        try:
            trigger_service.start_import_job("rewe")
            raise AssertionError("expected RuntimeError")
        except RuntimeError as exc:
            assert "already running" in str(exc)
    finally:
        release.set()

    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    assert state.status == "success"


def test_get_import_job_returns_snapshot_copy(monkeypatch):
    from api.services import trigger_service
    from workflows.progress_display import ProgressState

    def fake_run_lidl_initial(*, browser=None, cookies_file=None, country=None, output_dir=None, progress_listener=None):
        if progress_listener is not None:
            progress_listener(ProgressState(current=1, total=2, added=1, skipped=0, errors=0, items=4, current_receipt="r1"))
        return True

    monkeypatch.setattr(trigger_service, "run_lidl_initial", fake_run_lidl_initial)

    job_id = trigger_service.start_import_job("lidl")
    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    state.progress.current = 99

    fresh_state = trigger_service.get_import_job(job_id)
    assert fresh_state is not None
    assert fresh_state.progress.current == 1


def test_start_import_job_rolls_back_if_thread_start_fails(monkeypatch):
    from api.services import import_job_service
    from api.services import trigger_service

    before_count = len(import_job_service._jobs)

    def fake_start(self):
        raise RuntimeError("thread start failed")

    monkeypatch.setattr(import_job_service.Thread, "start", fake_start)

    try:
        trigger_service.start_import_job("lidl")
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "thread start failed" in str(exc)

    assert len(import_job_service._jobs) == before_count
