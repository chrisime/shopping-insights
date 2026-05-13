"""Workflow-nahe Hilfsfunktionen zur konsistenten Fehlerabbildung."""

from __future__ import annotations

import simplejson
from typing import Optional

import requests

from .workflow_constants import (
    REASON_KIND_LIDL_FETCH,
    REASON_KIND_REWE_DELTA_SCAN,
    REASON_KIND_REWE_PDF_PARSE,
)


def render_validation_reason(exc: Exception) -> str:
    """Render a validator exception into the normalized workflow reason string."""
    issues = getattr(exc, "issues", [])
    issues_text = "; ".join(issue.render() for issue in issues)
    return f"Validatorfehler: {issues_text}"



def render_exception_reason(exc: Exception, reason_kind: Optional[str] = None) -> str:
    """Render stable workflow reasons for known exception contexts."""
    if reason_kind == REASON_KIND_LIDL_FETCH:
        return _format_lidl_fetch_error(exc)
    if reason_kind == REASON_KIND_REWE_PDF_PARSE:
        return f"PDF konnte nicht gelesen werden: {exc}"
    if reason_kind == REASON_KIND_REWE_DELTA_SCAN:
        return f"Bon konnte nicht für Delta-Prüfung identifiziert werden: {exc}"
    return str(exc)


def _format_lidl_fetch_error(exc: Exception) -> str:
    """Render LIDL fetch-related exceptions into stable workflow reason strings."""
    if isinstance(exc, requests.exceptions.HTTPError):
        if exc.response is not None and exc.response.status_code == 401:
            return "Nicht autorisiert (401)"
        return f"HTTP-Fehler beim Abrufen: {exc}"
    if isinstance(exc, requests.exceptions.RequestException):
        return f"Fehler beim Abrufen: {exc}"
    if isinstance(exc, simplejson.JSONDecodeError):
        return f"JSON-Decodierungsfehler: {exc}"
    return f"Unerwarteter Fehler: {exc}"


