"""Service functions for fetch triggers."""

from __future__ import annotations

from typing import Any

from pydantic import SecretStr

from auth.rossmann_auth import authenticate_rossmann_account
from workflows.dm_workflow import run_dm_initial
from workflows.lidl_workflow import run_lidl_initial
from workflows.rewe_workflow import run_rewe_initial
from workflows.rossmann_workflow import run_rossmann_initial

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


def trigger_dm_fetch(
    days_back: int = 30,
    browser: str | None = None,
    cookies_file: str | None = None,
) -> dict[str, Any]:
    started = run_dm_initial(browser=browser, cookies_file=cookies_file)
    return {"data": {"retailer": "dm", "started": bool(started), "days_back": days_back}}


def trigger_rossmann_fetch(*, email: str, password: SecretStr, days_back: int = 30) -> dict[str, Any]:
    account = authenticate_rossmann_account(email, password.get_secret_value())
    started = run_rossmann_initial(
        account_id=account.account_id,
        account_hash=account.account_hash,
    )
    return {"data": {"retailer": "rossmann", "started": bool(started), "days_back": days_back}}
