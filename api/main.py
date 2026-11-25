"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp

from api.errors import ApiErrorCode, error_code_for_status
from api.frontend import register_frontend
from api.routes.exports import router as exports_router
from api.routes.dashboard import router as dashboard_router
from api.routes.items import router as items_router
from api.routes.kpis import router as kpis_router
from api.routes.imports import router as imports_router
from api.routes.receipts import router as receipts_router
from api.routes.triggers import router as triggers_router

app = FastAPI(title="Shopping Analyzer API")


@app.exception_handler(HTTPException)
async def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
    detail: object = exc.detail
    error_code = error_code_for_status(exc.status_code)
    if isinstance(detail, dict):
        candidate = detail.get("error_code")
        if isinstance(candidate, int):
            error_code = candidate
        detail = detail.get("detail", detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": int(error_code), "detail": detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    _request: Request, _exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error_code": int(ApiErrorCode.INVALID_REQUEST),
            "detail": "Request validation failed",
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error_code": int(ApiErrorCode.INTERNAL_ERROR),
            "detail": "Unexpected API error",
        },
    )


def _configure_cors(asgi_app: ASGIApp, /) -> CORSMiddleware:
    return CORSMiddleware(
        asgi_app,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.add_middleware(_configure_cors)
app.include_router(exports_router)
app.include_router(dashboard_router)
app.include_router(imports_router)
app.include_router(items_router)
app.include_router(kpis_router)
app.include_router(receipts_router)
app.include_router(triggers_router)
register_frontend(app)
