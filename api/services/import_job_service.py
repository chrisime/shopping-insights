"""In-memory registry for background import jobs."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock, Thread
from typing import Callable, Literal, cast
from uuid import uuid4

from workflows.progress_display import ProgressState


ImportJobStatus = Literal["running", "success", "error"]


@dataclass
class ImportJobSnapshot:
    job_id: str
    retailer: str
    status: ImportJobStatus
    progress: ProgressState
    message: str | None = None


_jobs: dict[str, ImportJobSnapshot] = {}
_jobs_lock = Lock()


def start_import_job(retailer: str) -> str:
    with _jobs_lock:
        active_job = next((job for job in _jobs.values() if job.status == "running"), None)
        if active_job is not None:
            raise RuntimeError(f"Import job already running: {active_job.job_id}")

    job_id = uuid4().hex
    _store_job(
        ImportJobSnapshot(
            job_id=job_id,
            retailer=retailer,
            status="running",
            progress=_empty_progress(),
        )
    )
    thread = Thread(target=_run_import_job, args=(job_id, retailer), daemon=True)
    thread.start()
    return job_id


def get_import_job(job_id: str) -> ImportJobSnapshot | None:
    with _jobs_lock:
        return _jobs.get(job_id)


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
        if started is False:
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


def _store_job(snapshot: ImportJobSnapshot) -> None:
    with _jobs_lock:
        _jobs[snapshot.job_id] = snapshot


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
        _jobs[job_id] = ImportJobSnapshot(
            job_id=current.job_id,
            retailer=retailer if retailer is not None else current.retailer,
            status=status if status is not None else current.status,
            progress=progress if progress is not None else current.progress,
            message=message if message is not None else current.message,
        )
