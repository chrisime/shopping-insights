"""Routes for starting imports and streaming job progress."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas.imports import ImportStartRequest, ImportStartResponse
from api.services import import_job_service
from workflows.workflow_errors import CONCURRENT_IMPORT_ERROR

router = APIRouter(prefix="/imports", tags=["imports"])

@router.post("/start", response_model=ImportStartResponse)
def start_import(payload: ImportStartRequest) -> ImportStartResponse:
    try:
        if payload.browser is None and payload.cookies_file is None and payload.customer_id is None:
            job_id = import_job_service.start_import_job(payload.retailer)
        else:
            job_id = import_job_service.start_import_job(
                payload.retailer,
                browser=payload.browser,
                cookies_file=payload.cookies_file,
                customer_id=payload.customer_id,
            )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error_code": CONCURRENT_IMPORT_ERROR.error_code, "detail": CONCURRENT_IMPORT_ERROR.detail},
        ) from exc
    return ImportStartResponse(job_id=job_id, retailer=payload.retailer)


@router.get("/{job_id}/events")
def import_events(job_id: str) -> StreamingResponse:
    if import_job_service.get_import_job(job_id) is None:
        raise HTTPException(status_code=404, detail="Import job not found")

    return StreamingResponse(_stream_import_job_events(job_id), media_type="text/event-stream")


def _stream_import_job_events(job_id: str):
    for event in import_job_service.iter_import_job_events(job_id):
        yield _format_sse_event(str(event["event"]), event["data"])


def _format_sse_event(event_name: str, payload: object) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
