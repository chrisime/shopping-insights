"""Workflow-nahe Hilfsfunktionen zur konsistenten Fehlerabbildung."""

from __future__ import annotations

from typing import Callable, Optional

from result_types import ReceiptParseResult

from .pipeline_types import ReceiptIssue

ReasonFormatter = Callable[[Exception], str]


def build_receipt_issue(
    source_id: str,
    reason: str,
    detail_key: str = "receipt_id",
) -> ReceiptIssue:
    """Create a structured workflow issue with a stable detail key."""
    return ReceiptIssue(
        source_id=source_id,
        reason=reason,
        detail_key=detail_key,
    )


def build_exception_issue(
    source_id: str,
    exc: Exception,
    detail_key: str = "receipt_id",
    reason_formatter: Optional[ReasonFormatter] = None,
) -> ReceiptIssue:
    """Map an exception into a structured workflow issue."""
    if reason_formatter is None:
        reason = str(exc)
    else:
        reason = reason_formatter(exc)
    return build_receipt_issue(
        source_id=source_id,
        reason=reason,
        detail_key=detail_key,
    )


def render_validation_reason(exc: Exception) -> str:
    """Render a validator exception into the normalized workflow reason string."""
    issues_text = "; ".join(issue.render() for issue in exc.issues)
    return f"Validatorfehler: {issues_text}"


def build_validation_issue(
    source_id: str,
    exc: Exception,
    detail_key: str = "receipt_id",
) -> ReceiptIssue:
    """Map a validator exception into a structured workflow issue."""
    return build_receipt_issue(
        source_id=source_id,
        reason=render_validation_reason(exc),
        detail_key=detail_key,
    )


def build_skip_result(reason: str) -> ReceiptParseResult:
    """Create a skipped parse result with a normalized skip reason."""
    return ReceiptParseResult(receipt_data=None, skip_reason=reason)


def build_exception_skip_result(
    exc: Exception,
    reason_formatter: Optional[ReasonFormatter] = None,
) -> ReceiptParseResult:
    """Map an exception into a skipped parse result."""
    if reason_formatter is None:
        reason = str(exc)
    else:
        reason = reason_formatter(exc)
    return build_skip_result(reason)


def build_validation_skip_result(exc: Exception) -> ReceiptParseResult:
    """Map a validator exception into a skipped parse result."""
    return build_skip_result(render_validation_reason(exc))

