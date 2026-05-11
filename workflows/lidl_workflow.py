"""Central LIDL workflows for initial import and incremental updates."""

import json
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup

from api.lidl_client import get_lidl_ticket, get_tickets_page, test_lidl_session
from auth.lidl_file_auth import diagnose_lidl_cookie_file
from auth.session_manager import setup_session
from config import LidlConfig
from parsing.lidl_items_extractor import extract_lidl_receipt_items
from parsing.lidl_receipt_parser import parse_lidl_ticket
from parsing.lidl_validator import LidlReceiptValidationError, validate_lidl_receipt_data
from reporting.lidl_api_reporting import (
    print_lidl_session_test_request_error,
    print_lidl_session_test_start,
    print_lidl_session_test_success,
)
from reporting.lidl_reporting import (
    print_lidl_checked_pages,
    print_lidl_existing_receipts_count,
    print_lidl_import_summary,
    print_lidl_missing_auth_source,
    print_lidl_new_receipts_count,
    print_lidl_processed_items,
    print_lidl_processed_pages,
    print_lidl_receipt_collection_result,
    print_lidl_receipt_collection_start,
    print_lidl_skipped_receipts,
    print_lidl_workflow_header,
    write_lidl_skipped_receipts_report,
)
from result_types import ReceiptParseResult, WorkflowSummary
from shared.ports import ReceiptStore
from storage import create_receipt_store

from .error_mapping import (
    build_exception_issue,
    build_exception_skip_result,
    build_validation_skip_result,
)
from .progress_display import ProgressState, ReceiptProgressDisplay
from .pipeline_runner import parse_receipts, persist_valid_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult


TicketDict = Dict[str, object]

__all__ = [
    "run_lidl_check",
    "run_lidl_initial",
    "run_lidl_update",
    "fetch_lidl_receipt_parse_result",
]


# ---------------------------------------------------------------------------
# Public use cases
# ---------------------------------------------------------------------------


def run_lidl_check(cookies_file: Optional[str] = None) -> bool:
    """Validate a LIDL cookie file."""
    return diagnose_lidl_cookie_file(cookies_file)


def run_lidl_initial(
    browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
    country: Optional[str] = None,
    write_backend: str = "json",
) -> bool:
    """Run the full historical LIDL import workflow."""
    print_lidl_workflow_header("=== INITIAL SETUP: Extrahiere alle LIDL-Kassenbons ===")
    session = _prepare_lidl_session(browser, cookies_file, country)
    if not session:
        return False
    store = create_receipt_store(write_backend)

    all_receipt_ids, total_pages = _collect_lidl_receipt_ids(session)
    snapshot = store.load_receipts_snapshot(retailer="lidl")

    print_lidl_existing_receipts_count(len(snapshot.receipts))
    new_receipt_ids = _filter_new_receipt_ids(all_receipt_ids, snapshot.existing_ids)
    print_lidl_new_receipts_count(len(new_receipt_ids))

    workflow_result = _run_lidl_receipt_pipeline(
        session=session,
        receipt_ids=new_receipt_ids,
        processed_pages=total_pages,
        store=store,
        receipts_file=snapshot.receipts_file,
    )
    _print_lidl_pipeline_result(workflow_result)
    _print_lidl_completion(
        title="\n=== INITIAL SETUP ABGESCHLOSSEN ===",
        total_items=workflow_result.summary.total_items,
        processed_pages=total_pages,
    )
    return workflow_result.success


def run_lidl_update(
    browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
    country: Optional[str] = None,
    write_backend: str = "json",
) -> bool:
    """Run the incremental LIDL update workflow."""
    print_lidl_workflow_header("=== UPDATE: Füge neue LIDL-Kassenbons hinzu ===")
    session = _prepare_lidl_session(browser, cookies_file, country)
    if not session:
        return False
    store = create_receipt_store(write_backend)

    recent_receipt_ids, checked_pages = _collect_lidl_receipt_ids(
        session,
        max_pages=LidlConfig.PAGES_TO_CHECK,
    )
    snapshot = store.load_receipts_snapshot(retailer="lidl")

    print_lidl_existing_receipts_count(len(snapshot.receipts))
    new_receipt_ids = _filter_new_receipt_ids(recent_receipt_ids, snapshot.existing_ids)
    print_lidl_checked_pages(checked_pages)
    print_lidl_new_receipts_count(len(new_receipt_ids))

    workflow_result = _run_lidl_receipt_pipeline(
        session=session,
        receipt_ids=new_receipt_ids,
        checked_pages=checked_pages,
        store=store,
        receipts_file=snapshot.receipts_file,
    )
    _print_lidl_pipeline_result(workflow_result)
    _print_lidl_completion(
        title="\n=== UPDATE ABGESCHLOSSEN ===",
        total_items=workflow_result.summary.total_items,
        checked_pages=checked_pages,
    )
    return workflow_result.success


# ---------------------------------------------------------------------------
# Public diagnostics helpers
# ---------------------------------------------------------------------------


def fetch_lidl_receipt_parse_result(
    session: requests.Session,
    receipt_id: str,
) -> ReceiptParseResult:
    """Fetch, parse and validate a single LIDL receipt inside the workflow layer."""
    return _fetch_lidl_receipt_parse_result(session, receipt_id)


# ---------------------------------------------------------------------------
# Receipt selection helpers
# ---------------------------------------------------------------------------


def _collect_lidl_receipt_ids(
    session: requests.Session,
    max_pages: Optional[int] = None,
) -> Tuple[List[str], int]:
    """Collect LIDL receipt IDs from all pages or only a limited number."""
    all_receipt_ids: List[str] = []
    page = 1
    processed_pages = 0

    print_lidl_receipt_collection_start(max_pages)

    while True:
        if max_pages is not None and page > max_pages:
            break

        tickets_data = get_tickets_page(session, page)
        if not tickets_data or "items" not in tickets_data:
            break

        tickets = tickets_data["items"]
        if not tickets:
            break

        all_receipt_ids.extend(_extract_receipt_ids_from_tickets(tickets))
        processed_pages = page

        if max_pages is not None and page >= max_pages:
            break

        total_count = tickets_data.get("totalCount", 0)
        page_size = tickets_data.get("size", 10)
        total_pages = (total_count + page_size - 1) // page_size
        if page >= total_pages:
            break

        page += 1

    print_lidl_receipt_collection_result(len(all_receipt_ids))
    return all_receipt_ids, processed_pages


# ---------------------------------------------------------------------------
# Session / setup helpers
# ---------------------------------------------------------------------------


def _setup_lidl_session(
    browser: Optional[str],
    cookies_file: Optional[str],
    country: Optional[str],
) -> Optional[requests.Session]:
    """Configure country and authenticate a LIDL session."""
    if country:
        LidlConfig.set_country(country)

    if browser:
        auth_method = browser
    elif cookies_file:
        auth_method = "file"
    else:
        print_lidl_missing_auth_source()
        return None

    return setup_session(
        retailer="lidl",
        auth_method=auth_method,
        cookies_file=cookies_file,
    )


def _prepare_lidl_session(
    browser: Optional[str],
    cookies_file: Optional[str],
    country: Optional[str],
) -> Optional[requests.Session]:
    """Build and verify the LIDL session required by initial/update workflows."""
    session = _setup_lidl_session(browser, cookies_file, country)
    if not session:
        return None
    if not _test_lidl_workflow_session(session):
        return None
    return session


def _test_lidl_workflow_session(session: requests.Session) -> bool:
    """Run the workflow-level LIDL session test including reporting side effects."""
    print_lidl_session_test_start()
    if not test_lidl_session(session):
        print_lidl_session_test_request_error(RuntimeError("LIDL-Session konnte nicht geprüft werden"))
        return False
    print_lidl_session_test_success()
    return True


def _print_lidl_pipeline_result(workflow_result: WorkflowResult) -> None:
    """Print skipped receipt details and the compact import summary."""
    print_lidl_skipped_receipts(
        workflow_result.skipped_details(),
        workflow_result.skipped_report_path,
    )
    print_lidl_import_summary(workflow_result.summary)


def _print_lidl_completion(
    title: str,
    total_items: int,
    checked_pages: Optional[int] = None,
    processed_pages: Optional[int] = None,
) -> None:
    """Print the workflow-specific completion footer for LIDL runs."""
    print_lidl_workflow_header(title)
    if processed_pages is not None:
        print_lidl_processed_pages(processed_pages)
    if checked_pages is not None:
        print_lidl_checked_pages(checked_pages)
    print_lidl_processed_items(total_items)


def _fetch_lidl_tickets(
    session: requests.Session,
    receipt_ids: List[str],
) -> Tuple[List[RawReceiptRecord], List[ReceiptIssue]]:
    """Fetch raw Lidl ticket payloads for all candidate receipt ids."""
    fetched_tickets: List[RawReceiptRecord] = []
    issues: List[ReceiptIssue] = []
    total_items = 0
    progress = ReceiptProgressDisplay(
        added_label="Abgerufen",
        items_label="Artikel",
    )
    total_receipts = len(receipt_ids)

    progress.render(
        ProgressState(0, total_receipts, 0, 0, 0, 0, "-")
    )

    for index, receipt_id in enumerate(receipt_ids, 1):
        progress.render(
            _build_lidl_fetch_state(
                current=index - 1,
                total=total_receipts,
                fetched_tickets=fetched_tickets,
                issues=issues,
                total_items=total_items,
                current_receipt=receipt_id,
            )
        )
        try:
            ticket_data = get_lidl_ticket(session, receipt_id)
            fetched_tickets.append(RawReceiptRecord(source_id=receipt_id, payload=ticket_data))
            total_items += _count_lidl_ticket_items(ticket_data)
        except requests.exceptions.HTTPError as exc:
            issues.append(
                build_exception_issue(
                    source_id=receipt_id,
                    exc=exc,
                    reason_formatter=_format_lidl_fetch_error,
                )
            )
        except requests.exceptions.RequestException as exc:
            issues.append(
                build_exception_issue(
                    source_id=receipt_id,
                    exc=exc,
                    reason_formatter=_format_lidl_fetch_error,
                )
            )
        except json.JSONDecodeError as exc:
            issues.append(
                build_exception_issue(
                    source_id=receipt_id,
                    exc=exc,
                    reason_formatter=_format_lidl_fetch_error,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(build_exception_issue(source_id=receipt_id, exc=exc))
        except Exception as exc:  # pragma: no cover - defensive fallback
            issues.append(
                build_exception_issue(
                    source_id=receipt_id,
                    exc=exc,
                    reason_formatter=_format_lidl_fetch_error,
                )
            )

        progress.render(
            _build_lidl_fetch_state(
                current=index,
                total=total_receipts,
                fetched_tickets=fetched_tickets,
                issues=issues,
                total_items=total_items,
                current_receipt=receipt_id,
            )
        )
        if LidlConfig.REQUEST_DELAY > 0:
            time.sleep(LidlConfig.REQUEST_DELAY)

    progress.close()
    return fetched_tickets, issues


def _count_lidl_ticket_items(ticket_data: Dict[str, object]) -> int:
    """Return the number of extractable items in a raw Lidl ticket payload."""
    html_content = ticket_data.get("htmlPrintedReceipt")
    if not isinstance(html_content, str) or not html_content.strip():
        return 0

    soup = BeautifulSoup(html_content, "html.parser")
    return len(extract_lidl_receipt_items(soup))


def _build_lidl_fetch_state(
    current: int,
    total: int,
    fetched_tickets: Sequence[RawReceiptRecord],
    issues: Sequence[ReceiptIssue],
    total_items: int,
    current_receipt: str,
) -> ProgressState:
    """Create a consistent progress snapshot for the LIDL fetch stage."""
    return ProgressState(
        current=current,
        total=total,
        added=len(fetched_tickets),
        skipped=len(issues),
        errors=len(issues),
        items=total_items,
        current_receipt=current_receipt,
    )


# ---------------------------------------------------------------------------
# Pipeline assembly helpers
# ---------------------------------------------------------------------------


def _run_lidl_receipt_pipeline(
    session: requests.Session,
    receipt_ids: List[str],
    store: ReceiptStore,
    receipts_file: str,
    checked_pages: Optional[int] = None,
    processed_pages: Optional[int] = None,
) -> WorkflowResult:
    """Run the shared LIDL fetch/parse/validate/persist pipeline and return a normalized result."""
    fetched_tickets, fetch_issues = _fetch_lidl_tickets(session, receipt_ids)
    parse_result = _parse_lidl_receipts(fetched_tickets)
    validation_result = _validate_lidl_receipts(parse_result.records)
    persist_result = persist_valid_receipts(
        validation_result.records,
        retailer="lidl",
        store=store,
    )

    skipped_issues = [
        *fetch_issues,
        *parse_result.issues,
        *validation_result.issues,
    ]
    skipped_details = [issue.as_detail() for issue in skipped_issues]
    report_path = write_lidl_skipped_receipts_report(skipped_details)

    return WorkflowResult(
        success=True,
        summary=WorkflowSummary(
            retailer="lidl",
            processed_count=persist_result.processed_count,
            skipped_count=len(skipped_issues),
            total_receipts=persist_result.total_receipts,
            receipts_file=receipts_file,
            total_items=validation_result.total_items,
            checked_pages=checked_pages,
            processed_pages=processed_pages,
        ),
        skipped_issues=skipped_issues,
        skipped_report_path=report_path,
    )


def _parse_lidl_receipts(raw_records: Sequence[RawReceiptRecord]):
    """Parse fetched LIDL raw records via the shared parse stage."""
    return parse_receipts(
        raw_records,
        parse_record=_parse_lidl_raw_record,
    )


def _validate_lidl_receipts(parsed_records):
    """Validate parsed LIDL receipts via the shared validation stage."""
    return validate_receipts(
        parsed_records,
        validate_receipt=validate_lidl_receipt_data,
        validation_error_types=(LidlReceiptValidationError,),
    )


def _parse_lidl_raw_record(raw_record: RawReceiptRecord) -> dict:
    """Parse a fetched LIDL raw record into the normalized receipt schema."""
    return parse_lidl_ticket(raw_record.payload, raw_record.source_id)


def _fetch_lidl_receipt_parse_result(
    session: requests.Session,
    receipt_id: str,
) -> ReceiptParseResult:
    """Fetch, parse and validate a single LIDL receipt inside the workflow layer."""
    try:
        ticket_data = get_lidl_ticket(session, receipt_id)
    except requests.exceptions.HTTPError as exc:
        return build_exception_skip_result(exc, reason_formatter=_format_lidl_fetch_error)
    except requests.exceptions.RequestException as exc:
        return build_exception_skip_result(exc, reason_formatter=_format_lidl_fetch_error)
    except json.JSONDecodeError as exc:
        return build_exception_skip_result(exc, reason_formatter=_format_lidl_fetch_error)
    except (KeyError, TypeError, ValueError) as exc:
        return build_exception_skip_result(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return build_exception_skip_result(exc, reason_formatter=_format_lidl_fetch_error)

    try:
        receipt_data = parse_lidl_ticket(ticket_data, receipt_id)
        validate_lidl_receipt_data(receipt_data)
        return ReceiptParseResult(receipt_data=receipt_data)
    except LidlReceiptValidationError as exc:
        return build_validation_skip_result(exc)
    except (KeyError, TypeError, ValueError) as exc:
        return build_exception_skip_result(exc)


# ---------------------------------------------------------------------------
# Single-receipt helpers / selection utilities
# ---------------------------------------------------------------------------


def _extract_receipt_ids_from_tickets(tickets: List[TicketDict]) -> List[str]:
    """Extract receipt IDs for tickets that have HTML receipts."""
    receipt_ids = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue

        if "ticket" in ticket:
            ticket_data = ticket["ticket"]
            receipt_id = ticket_data.get("id", "")
            has_html = ticket_data.get("isHtml", False)
        else:
            receipt_id = ticket.get("id", "")
            has_html = ticket.get("isHtml", False)

        if receipt_id and has_html:
            receipt_ids.append(str(receipt_id))

    return receipt_ids


def _filter_new_receipt_ids(
    receipt_ids: Sequence[str],
    existing_ids: Iterable[str],
) -> List[str]:
    """Return only receipt IDs that are not already stored."""
    existing_id_set = set(existing_ids)
    return [receipt_id for receipt_id in receipt_ids if receipt_id not in existing_id_set]


def _format_lidl_fetch_error(exc: Exception) -> str:
    """Render LIDL fetch-related exceptions into stable workflow reason strings."""
    if isinstance(exc, requests.exceptions.HTTPError):
        if exc.response is not None and exc.response.status_code == 401:
            return "Nicht autorisiert (401)"
        return f"HTTP-Fehler beim Abrufen: {exc}"
    if isinstance(exc, requests.exceptions.RequestException):
        return f"Fehler beim Abrufen: {exc}"
    if isinstance(exc, json.JSONDecodeError):
        return f"JSON-Decodierungsfehler: {exc}"
    return f"Unerwarteter Fehler: {exc}"


