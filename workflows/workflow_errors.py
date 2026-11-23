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
    "missing_auth": WorkflowErrorInfo("lidl", 4007, "LIDL benötigt --cookies-file oder --browser."),
    "browser_no_cookies": WorkflowErrorInfo("lidl", 4008, "LIDL-Browserprofil konnte keine Cookies liefern."),
    "session_check_failed": WorkflowErrorInfo("lidl", 4009, "LIDL-Session konnte nicht geprüft werden."),
}

REWE_INITIAL_ERROR_DETAILS: dict[int, WorkflowErrorInfo] = {
    2201: WorkflowErrorInfo("rewe", 4010, "REWE benötigt --cookies-file oder --browser."),
    2202: WorkflowErrorInfo("rewe", 4011, "REWE-Cookies aus der Datei konnten nicht geladen werden."),
    2203: WorkflowErrorInfo("rewe", 4012, "REWE-Browserprofil konnte keine Cookies liefern."),
    2204: WorkflowErrorInfo("rewe", 4013, "REWE customerId konnte aus der Datei nicht gelesen werden."),
    2205: WorkflowErrorInfo("rewe", 4014, "Browserprofil gesperrt"),
    2206: WorkflowErrorInfo("rewe", 4015, "REWE-Session aus der Datei ist ungültig oder abgelaufen."),
    2207: WorkflowErrorInfo("rewe", 4016, "REWE-Browser-Session ist ungültig oder abgelaufen."),
    2208: WorkflowErrorInfo("rewe", 5002, "REWE ZIP-Abruf mit customerId fehlgeschlagen."),
    2209: WorkflowErrorInfo("rewe", 5003, "REWE ZIP-Abruf ohne customerId fehlgeschlagen."),
}

ROSSMANN_INITIAL_ERROR_DETAILS: dict[int, WorkflowErrorInfo] = {
    2401: WorkflowErrorInfo("rossmann", 4017, "Rossmann benötigt --cookies-file oder --browser."),
    2402: WorkflowErrorInfo("rossmann", 4018, "Rossmann-Cookies aus der Datei konnten nicht geladen werden."),
    2403: WorkflowErrorInfo("rossmann", 4019, "Rossmann-Browserprofil konnte keine Cookies liefern."),
    2404: WorkflowErrorInfo("rossmann", 4020, "Rossmann-Session ist ungültig (kein anybill-Token mintbar)."),
    2405: WorkflowErrorInfo("rossmann", 4021, "Rossmann-accountId/accountHash konnten nicht ermittelt werden."),
    2406: WorkflowErrorInfo("rossmann", 5004, "anybill-Abruf der Belegliste fehlgeschlagen."),
    2407: WorkflowErrorInfo("rossmann", 4022, "Rossmann-Anmeldung fehlgeschlagen. Prüfe E-Mail und Passwort."),
    2408: WorkflowErrorInfo("rossmann", 5005, "Rossmann konnte nicht alle neuen Belege laden. Starte den Import erneut."),
}

DM_INITIAL_ERROR_DETAILS: dict[int, WorkflowErrorInfo] = {
    2301: WorkflowErrorInfo("dm", 4023, "dm benötigt --cookies-file oder --browser."),
    2302: WorkflowErrorInfo("dm", 4024, "dm-Cookies aus der Datei konnten nicht geladen werden."),
    2303: WorkflowErrorInfo("dm", 4025, "dm-Browserprofil konnte keine Cookies liefern."),
    2304: WorkflowErrorInfo("dm", 4026, "dm-Session ist ungültig oder abgelaufen (kein Access-Token)."),
    2305: WorkflowErrorInfo("dm", 5006, "dm-Access-Token konnte nicht ausgestellt werden."),
    2306: WorkflowErrorInfo("dm", 5007, "dm-Kaufhistorie konnte nicht abgerufen werden."),
}

CONCURRENT_IMPORT_ERROR = WorkflowErrorInfo("shared", 4003, "Import bereits aktiv")

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


def dm_initial_error(error_code: int) -> WorkflowErrorInfo:
    return DM_INITIAL_ERROR_DETAILS[error_code]


def rossmann_initial_error(error_code: int) -> WorkflowErrorInfo:
    return ROSSMANN_INITIAL_ERROR_DETAILS[error_code]
