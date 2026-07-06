"""Shared workflow error codes and transient failure details."""

from __future__ import annotations

from dataclasses import dataclass
from threading import local


@dataclass(frozen=True)
class WorkflowErrorInfo:
    retailer: str
    error_code: int
    detail: str


LIDL_INITIAL_ERROR_DETAILS: dict[str, WorkflowErrorInfo] = {
    "missing_auth": WorkflowErrorInfo("lidl", 2101, "LIDL benötigt --cookies-file oder --browser."),
    "browser_no_cookies": WorkflowErrorInfo("lidl", 2102, "LIDL-Browserprofil konnte keine Cookies liefern."),
    "session_check_failed": WorkflowErrorInfo("lidl", 2103, "LIDL-Session konnte nicht geprüft werden."),
}

REWE_INITIAL_ERROR_DETAILS: dict[int, WorkflowErrorInfo] = {
    2201: WorkflowErrorInfo("rewe", 2201, "REWE benötigt --cookies-file oder --browser."),
    2202: WorkflowErrorInfo("rewe", 2202, "REWE-Cookies aus der Datei konnten nicht geladen werden."),
    2203: WorkflowErrorInfo("rewe", 2203, "REWE-Browserprofil konnte keine Cookies liefern."),
    2204: WorkflowErrorInfo("rewe", 2204, "REWE customerId konnte aus der Datei nicht gelesen werden."),
    2205: WorkflowErrorInfo("rewe", 2205, "Browserprofil gesperrt"),
    2206: WorkflowErrorInfo("rewe", 2206, "REWE-Session aus der Datei ist ungültig oder abgelaufen."),
    2207: WorkflowErrorInfo("rewe", 2207, "REWE-Browser-Session ist ungültig oder abgelaufen."),
    2208: WorkflowErrorInfo("rewe", 2208, "REWE ZIP-Abruf mit customerId fehlgeschlagen."),
    2209: WorkflowErrorInfo("rewe", 2209, "REWE ZIP-Abruf ohne customerId fehlgeschlagen."),
}

CONCURRENT_IMPORT_ERROR = WorkflowErrorInfo("shared", 4091, "Import bereits aktiv")

_state = local()


def set_last_workflow_error(info: WorkflowErrorInfo | None) -> None:
    if info is None:
        clear_last_workflow_error()
        return
    _state.last_error = info


def get_last_workflow_error() -> WorkflowErrorInfo | None:
    return getattr(_state, "last_error", None)


def clear_last_workflow_error() -> None:
    if hasattr(_state, "last_error"):
        delattr(_state, "last_error")


def lidl_initial_error(key: str) -> WorkflowErrorInfo:
    return LIDL_INITIAL_ERROR_DETAILS[key]


def rewe_initial_error(error_code: int) -> WorkflowErrorInfo:
    return REWE_INITIAL_ERROR_DETAILS[error_code]
