"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes.ui import router as ui_router

app = FastAPI(title="Shopping Analyzer API")
app.include_router(ui_router)
