"""Service functions for fetch triggers."""

from __future__ import annotations

from typing import Any

from workflows.lidl_workflow import run_lidl_initial
from workflows.rewe_workflow import run_rewe_initial

from api.services.import_job_service import get_import_job, start_import_job


def trigger_lidl_fetch(days_back: int = 30, browser: str | None = None, cookies_file: str | None = None) -> dict[str, Any]:
    started = run_lidl_initial(browser=browser, cookies_file=cookies_file)
    return {"data": {"retailer": "lidl", "started": bool(started), "days_back": days_back}}


def trigger_rewe_fetch(
    days_back: int = 30,
    browser: str | None = None,
    cookies_file: str | None = None,
    customer_id: str | None = None,
) -> dict[str, Any]:
    started = run_rewe_initial(browser=browser, cookies_file=cookies_file, customer_id=customer_id)
    return {"data": {"retailer": "rewe", "started": bool(started), "days_back": days_back}}
