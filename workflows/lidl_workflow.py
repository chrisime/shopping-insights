"""Central LIDL workflow for synchronizing receipt state from the Lidl API."""

import simplejson
import time
from typing import Dict, List, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup

from api.lidl_client import get_lidl_ticket, get_tickets_page, test_lidl_session
from auth.session_manager import setup_session
from config import LidlConfig
from config import storage_config
from parsing.lidl_items_extractor import extract_lidl_receipt_items
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
from result_types import WorkflowSummary
from shared.receipt_hashes import calculate_receipt_payload_hash
from shared.receipt_store import ReceiptStore
from storage import create_receipt_store

from .error_mapping import (
    render_exception_reason,
)
from .progress_display import ProgressState, ReceiptProgressDisplay
from .pipeline_runner import parse_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult
from .workflow_constants import RETAILER_LIDL, REASON_KIND_LIDL_FETCH


__all__ = [
    "run_lidl_sync",
]


def run_lidl_sync(
    browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
    country: Optional[str] = None,
) -> bool:
    """Synchronize Lidl receipts by scanning all pages and importing only new receipts."""
    start_title = "=== SYNC: Synchronisiere LIDL-Kassenbons ==="
    completion_title = "\n=== SYNC ABGESCHLOSSEN ==="
    print_lidl_workflow_header(start_title)
    session = _prepare_lidl_session(browser, cookies_file, country)
    if not session:
        return False

    store = create_receipt_store()
    discovered_receipt_ids, page_count = _collect_lidl_receipt_ids(session)
    existing_receipt_ids = store.find_existing_ids(retailer=RETAILER_LIDL)
    receipt_ids = _filter_new_lidl_receipt_ids(discovered_receipt_ids, existing_receipt_ids)

    print_lidl_existing_receipts_count(len(existing_receipt_ids))
    print_lidl_checked_pages(page_count)
    print_lidl_new_receipts_count(len(receipt_ids))

    workflow_result = _run_lidl_receipt_pipeline(
        session=session,
        receipt_ids=receipt_ids,
        checked_pages=page_count,
        store=store,
        receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
    )
    _print_lidl_pipeline_result(workflow_result)
    _print_lidl_completion(
        title=completion_title,
        total_items=workflow_result.summary.total_items,
        checked_pages=page_count,
    )
    return workflow_result.success



def _collect_lidl_receipt_ids(
    session: requests.Session,
    max_pages: Optional[int] = None,
) -> Tuple[List[str], int]:
    """Collect LIDL receipt ids from all pages or only a limited number."""
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
        retailer=RETAILER_LIDL,
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
    skipped_details = [issue.as_detail() for issue in workflow_result.skipped_issues]
    print_lidl_skipped_receipts(skipped_details, workflow_result.skipped_report_path)
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

    progress.render(ProgressState(0, total_receipts, 0, 0, 0, 0, "-"))

    for index, receipt_id in enumerate(receipt_ids, 1):
        current = index - 1
        progress.render(
            ProgressState(
                current=current,
                total=total_receipts,
                added=len(fetched_tickets),
                skipped=len(issues),
                errors=len(issues),
                items=total_items,
                current_receipt=receipt_id,
            )
        )
        try:
            ticket_data = get_lidl_ticket(session, receipt_id)
            fetched_tickets.append(RawReceiptRecord(source_id=receipt_id, payload=ticket_data))
            total_items += _count_lidl_ticket_items(ticket_data)
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException, simplejson.JSONDecodeError) as exc:
            issues.append(_build_lidl_fetch_issue(receipt_id, exc, fetch_related=True))
        except (KeyError, TypeError, ValueError) as exc:
            issues.append(_build_lidl_fetch_issue(receipt_id, exc))
        except Exception as exc:  # pragma: no cover - defensive fallback
            issues.append(_build_lidl_fetch_issue(receipt_id, exc, fetch_related=True))

        progress.render(
            ProgressState(
                current=index,
                total=total_receipts,
                added=len(fetched_tickets),
                skipped=len(issues),
                errors=len(issues),
                items=total_items,
                current_receipt=receipt_id,
            )
        )
        if LidlConfig.REQUEST_DELAY > 0:
            time.sleep(LidlConfig.REQUEST_DELAY)

    progress.close()
    return fetched_tickets, issues


def _build_lidl_fetch_issue(receipt_id: str, exc: Exception, fetch_related: bool = False) -> ReceiptIssue:
    """Build a normalized workflow issue for LIDL ticket fetch failures."""
    reason_kind = REASON_KIND_LIDL_FETCH if fetch_related else None
    return ReceiptIssue(source_id=receipt_id, reason=render_exception_reason(exc, reason_kind))


def _count_lidl_ticket_items(ticket_data: Dict[str, object]) -> int:
    """Return the number of extractable items in a raw Lidl ticket payload."""
    html_content = ticket_data.get("htmlPrintedReceipt")
    if not isinstance(html_content, str) or not html_content.strip():
        return 0

    soup = BeautifulSoup(html_content, "html.parser")
    return len(extract_lidl_receipt_items(soup))



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
    parse_result = parse_receipts(fetched_tickets, retailer=RETAILER_LIDL)
    validation_result = validate_receipts(parse_result.records, retailer=RETAILER_LIDL)
    receipts_to_persist = _prepare_lidl_receipts_for_persistence(validation_result.records)
    persist_result = store.persist_receipts(receipts_to_persist, retailer=RETAILER_LIDL)

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
            retailer=RETAILER_LIDL,
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



def _extract_receipt_ids_from_tickets(tickets: List[Dict[str, object]]) -> List[str]:
    """Extract receipt ids for tickets that have an HTML receipt representation."""
    receipt_ids: List[str] = []
    for ticket in tickets:
        ticket_data = _extract_lidl_ticket_data(ticket)
        if ticket_data is None:
            continue

        receipt_id = ticket_data.get("id", "")
        has_html = ticket_data.get("isHtml", False)
        if receipt_id and has_html:
            receipt_ids.append(str(receipt_id))

    return receipt_ids


def _extract_lidl_ticket_data(ticket: object) -> Optional[Dict[str, object]]:
    if not isinstance(ticket, dict):
        return None
    if "ticket" not in ticket:
        return ticket
    nested_ticket = ticket.get("ticket")
    if not isinstance(nested_ticket, dict):
        return None
    return nested_ticket


def _filter_new_lidl_receipt_ids(
    discovered_receipt_ids: Sequence[str],
    existing_receipt_ids: set[str],
) -> List[str]:
    """Return only new receipt ids and keep their original discovery order."""
    new_receipt_ids: List[str] = []
    seen_receipt_ids: set[str] = set()
    for receipt_id in discovered_receipt_ids:
        if receipt_id in existing_receipt_ids or receipt_id in seen_receipt_ids:
            continue
        seen_receipt_ids.add(receipt_id)
        new_receipt_ids.append(receipt_id)
    return new_receipt_ids


def _prepare_lidl_receipts_for_persistence(
    receipts: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    """Attach payload_hash to validated Lidl receipts before persistence."""
    prepared_receipts: List[Dict[str, object]] = []
    for receipt in receipts:
        prepared_receipt = dict(receipt)
        prepared_receipt["payload_hash"] = calculate_receipt_payload_hash(prepared_receipt)
        prepared_receipts.append(prepared_receipt)
    return prepared_receipts
