"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.exports import router as exports_router
from api.routes.dashboard import router as dashboard_router
from api.routes.items import router as items_router
from api.routes.kpis import router as kpis_router
from api.routes.imports import router as imports_router
from api.routes.receipts import router as receipts_router
from api.routes.triggers import router as triggers_router

app = FastAPI(title="Shopping Analyzer API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(exports_router)
app.include_router(dashboard_router)
app.include_router(imports_router)
app.include_router(items_router)
app.include_router(kpis_router)
app.include_router(receipts_router)
app.include_router(triggers_router)
