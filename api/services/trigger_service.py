"""Service functions for fetch triggers."""

from __future__ import annotations

from typing import Any

from workflows.lidl_workflow import run_lidl_initial
from workflows.rewe_workflow import run_rewe_initial


def trigger_lidl_fetch(days_back: int = 30) -> dict[str, Any]:
    started = run_lidl_initial()
    return {"data": {"retailer": "lidl", "started": bool(started), "days_back": days_back}}


def trigger_rewe_fetch(days_back: int = 30) -> dict[str, Any]:
    started = run_rewe_initial()
    return {"data": {"retailer": "rewe", "started": bool(started), "days_back": days_back}}
