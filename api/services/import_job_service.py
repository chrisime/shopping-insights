"""In-memory registry for background import jobs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Condition, Lock, Thread
from typing import Callable, Literal, cast
from uuid import uuid4

from workflows.progress_display import ProgressState


ImportJobStatus = Literal["running", "success", "error"]


@dataclass(frozen=True)
class ImportJobSnapshot:
    job_id: str
    retailer: str
    status: ImportJobStatus
    progress: ProgressState
    message: str | None = None


_jobs: dict[str, ImportJobSnapshot] = {}
_job_events: dict[str, list[dict[str, object]]] = {}
_job_conditions: dict[str, Condition] = {}
_jobs_lock = Lock()


def start_import_job(retailer: str) -> str:
    with _jobs_lock:
        active_job = next((job for job in _jobs.values() if job.status == "running"), None)
        if active_job is not None:
            raise RuntimeError(f"Import job already running: {active_job.job_id}")

        job_id = uuid4().hex
        _jobs[job_id] = ImportJobSnapshot(
            job_id=job_id,
            retailer=retailer,
            status="running",
            progress=_empty_progress(),
        )
        _job_events[job_id] = []
        _job_conditions[job_id] = Condition()

    _append_job_event(job_id, "progress", get_import_job(job_id))

    thread = Thread(target=_run_import_job, args=(job_id, retailer), daemon=True)
    try:
        thread.start()
    except Exception:
        with _jobs_lock:
            _jobs.pop(job_id, None)
            _job_events.pop(job_id, None)
            _job_conditions.pop(job_id, None)
        raise
    return job_id


def get_import_job(job_id: str) -> ImportJobSnapshot | None:
    with _jobs_lock:
        current = _jobs.get(job_id)
        if current is None:
            return None
        return ImportJobSnapshot(
            job_id=current.job_id,
            retailer=current.retailer,
            status=current.status,
            progress=replace(current.progress),
            message=current.message,
        )


def iter_import_job_events(job_id: str):
    condition = _get_job_condition(job_id)
    if condition is None:
        yield {"event": "error", "data": {"job_id": job_id, "message": "job_not_found"}}
        return

    next_index = 0
    while True:
        with condition:
            events = _job_events.get(job_id)
            if events is None:
                yield {"event": "error", "data": {"job_id": job_id, "message": "job_not_found"}}
                return

            if next_index < len(events):
                event = events[next_index]
                next_index += 1
            else:
                condition.wait()
                continue

        yield event
        if event["event"] in {"success", "error"}:
            return


def _run_import_job(job_id: str, retailer: str) -> None:
    progress_listener = _build_progress_listener(job_id, retailer)
    try:
        from api.services import trigger_service

        if retailer == "lidl":
            started = cast(Callable[..., object], trigger_service.run_lidl_initial)(progress_listener=progress_listener)
        elif retailer == "rewe":
            started = cast(Callable[..., object], trigger_service.run_rewe_initial)(progress_listener=progress_listener)
        else:
            raise ValueError(f"Unsupported retailer: {retailer}")
        if not started:
            raise RuntimeError(f"Import workflow returned False for retailer: {retailer}")
    except Exception as exc:
        _update_job(job_id, status="error", message=str(exc))
    else:
        _update_job(job_id, status="success", message=None)


def _build_progress_listener(job_id: str, retailer: str) -> Callable[[ProgressState], None]:
    def progress_listener(progress: ProgressState) -> None:
        _update_job(job_id, retailer=retailer, progress=progress)

    return progress_listener


def _empty_progress() -> ProgressState:
    return ProgressState(current=0, total=0, added=0, skipped=0, errors=0, items=0, current_receipt="-")


def _get_job_condition(job_id: str) -> Condition | None:
    with _jobs_lock:
        return _job_conditions.get(job_id)


def _append_job_event(job_id: str, event_type: str, snapshot: ImportJobSnapshot | None) -> None:
    if snapshot is None:
        return

    condition = _get_job_condition(job_id)
    if condition is None:
        return

    event = {"event": event_type, "data": _snapshot_to_dict(snapshot)}
    with condition:
        with _jobs_lock:
            events = _job_events.get(job_id)
            if events is None:
                return
            events.append(event)
        condition.notify_all()


def _snapshot_to_dict(snapshot: ImportJobSnapshot) -> dict[str, object]:
    return {
        "job_id": snapshot.job_id,
        "retailer": snapshot.retailer,
        "status": snapshot.status,
        "progress": {
            "current": snapshot.progress.current,
            "total": snapshot.progress.total,
            "added": snapshot.progress.added,
            "skipped": snapshot.progress.skipped,
            "errors": snapshot.progress.errors,
            "items": snapshot.progress.items,
            "current_receipt": snapshot.progress.current_receipt,
        },
        "message": snapshot.message,
    }


def _update_job(
    job_id: str,
    *,
    retailer: str | None = None,
    status: ImportJobStatus | None = None,
    progress: ProgressState | None = None,
    message: str | None = None,
) -> None:
    with _jobs_lock:
        current = _jobs.get(job_id)
        if current is None:
            return
        updated = ImportJobSnapshot(
            job_id=current.job_id,
            retailer=retailer if retailer is not None else current.retailer,
            status=status if status is not None else current.status,
            progress=replace(progress) if progress is not None else replace(current.progress),
            message=message if message is not None else current.message,
        )
        _jobs[job_id] = updated

    event_type = status if status in {"success", "error"} else "progress"
    _append_job_event(job_id, event_type, updated)
