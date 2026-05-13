"""Central REWE workflows for eBon download, PDF import and diagnostics."""

from pathlib import Path
from typing import Optional, Sequence
import zipfile

import requests

from api.rewe_client import download_receipts_zip, test_rewe_session
from auth.rewe_customer_id import cache_customer_id, resolve_rewe_customer_id
from auth.session_manager import setup_session
from reporting.rewe_api_reporting import (
    print_rewe_session_test_start, print_rewe_session_test_success,
    print_rewe_zip_saved
)
from reporting.rewe_workflow_reporting import (
    print_rewe_missing_auth_source,
    print_rewe_no_pdfs_found,
    print_rewe_import_summary,
    print_rewe_skipped_receipts,
    print_rewe_update_no_delta,
    print_rewe_zip_extracted,
    write_rewe_skipped_receipts_report,
)
from result_types import WorkflowSummary
from shared.receipt_store import ReceiptStore
from storage import create_receipt_store, resolve_receipt_store_target

from .pipeline_runner import parse_receipts, persist_valid_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult
from .workflow_constants import RETAILER_REWE, REASON_KIND_REWE_PDF_PARSE

REWE_DEFAULT_OUTPUT_DIR = "tmp/rewe"

__all__ = [
    "run_rewe_initial",
    "run_rewe_update",
]

def run_rewe_initial(
        customer_id: Optional[str] = None,
        browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        output_dir: str = REWE_DEFAULT_OUTPUT_DIR,
        write_backend: str = "json",
) -> bool:
    """Run the full REWE eBon workflow: download ZIP, extract PDFs, import JSON."""

    store = create_receipt_store(write_backend)
    receipts_file = resolve_receipt_store_target(write_backend, retailer=RETAILER_REWE)
    prepared_session = _prepare_rewe_import_session(
        customer_id=customer_id,
        browser=browser,
        cookies_file=cookies_file,
        output_dir=output_dir,
    )
    if not prepared_session:
        return False

    session, resolved_customer_id = prepared_session
    base_output_dir = Path(output_dir)
    zip_path = base_output_dir / "receipts.zip"
    pdf_output_dir = base_output_dir / "pdfs"

    if not _download_and_extract_rewe_zip(session, resolved_customer_id, zip_path, pdf_output_dir):
        return False

    workflow_result = _run_rewe_pdf_import_pipeline(
        pdf_output_dir,
        retailer=RETAILER_REWE,
        store=store,
        receipts_file=receipts_file,
    )
    print_rewe_import_summary(workflow_result.summary)

    if resolved_customer_id:
        cache_customer_id(resolved_customer_id, str(base_output_dir))
    return workflow_result.success



def run_rewe_update(
        customer_id: Optional[str] = None,
        browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        output_dir: str = REWE_DEFAULT_OUTPUT_DIR,
        write_backend: str = "json",
) -> bool:
    """Re-import all locally downloaded REWE PDFs into the configured store via upsert."""
    _ = customer_id, browser, cookies_file
    print_rewe_update_no_delta()
    store = create_receipt_store(write_backend)
    receipts_file = resolve_receipt_store_target(write_backend, retailer=RETAILER_REWE)
    pdf_output_dir = Path(output_dir) / "pdfs"
    workflow_result = _run_rewe_pdf_import_pipeline(
        pdf_output_dir,
        retailer=RETAILER_REWE,
        store=store,
        receipts_file=receipts_file,
    )

    print_rewe_import_summary(workflow_result.summary)
    return workflow_result.success



def _run_rewe_pdf_import_pipeline(
        pdf_dir: Path,
        store: ReceiptStore,
        receipts_file: str,
        file_path: Optional[str] = None,
        retailer: str = RETAILER_REWE,
        pdf_paths: Optional[Sequence[Path]] = None,
        prefilter_issues: Optional[Sequence[ReceiptIssue]] = None,
        existing_total_receipts: Optional[int] = None,
) -> WorkflowResult:
    """Parse, validate and persist extracted REWE PDFs and return a normalized workflow result."""
    active_pdf_paths = list(pdf_paths) if pdf_paths is not None else sorted(pdf_dir.glob("*.pdf"))
    initial_issues = list(prefilter_issues or [])
    if not active_pdf_paths:
        if pdf_paths is None:
            print_rewe_no_pdfs_found(pdf_dir)
            return WorkflowResult(
                success=False,
                summary=WorkflowSummary(
                    retailer=retailer,
                    processed_count=0,
                    skipped_count=0,
                    total_receipts=0,
                    receipts_file=receipts_file,
                    total_items=0,
                ),
                skipped_issues=[],
                skipped_report_path=None,
            )

        return _build_rewe_prefilter_only_result(
            pdf_dir=pdf_dir,
            receipts_file=receipts_file,
            retailer=retailer,
            initial_issues=initial_issues,
            existing_total_receipts=existing_total_receipts,
        )

    raw_pdf_records = [
        RawReceiptRecord(source_id=pdf_path.name, payload=pdf_path)
        for pdf_path in active_pdf_paths
    ]
    parse_result = parse_receipts(
        raw_pdf_records,
        retailer=RETAILER_REWE,
        detail_key="file",
        unexpected_error_kind=REASON_KIND_REWE_PDF_PARSE,
    )
    validation_result = validate_receipts(
        parse_result.records,
        retailer=RETAILER_REWE,
        detail_key="file",
    )
    persist_result = persist_valid_receipts(
        validation_result.records,
        retailer=retailer,
        store=store,
        file_path=file_path,
    )
    skipped_issues = [*initial_issues, *parse_result.issues, *validation_result.issues]
    skipped_details = [issue.as_detail() for issue in skipped_issues]
    skip_report_path = write_rewe_skipped_receipts_report(pdf_dir, skipped_details)
    print_rewe_skipped_receipts(skipped_details, skip_report_path)
    return WorkflowResult(
        success=True,
        summary=WorkflowSummary(
            retailer=retailer,
            processed_count=persist_result.processed_count,
            skipped_count=len(skipped_issues),
            total_receipts=persist_result.total_receipts,
            receipts_file=receipts_file,
            total_items=validation_result.total_items,
        ),
        skipped_issues=skipped_issues,
        skipped_report_path=skip_report_path,
    )


def _build_rewe_prefilter_only_result(
        pdf_dir: Path,
        receipts_file: str,
        retailer: str,
        initial_issues: Sequence[ReceiptIssue],
        existing_total_receipts: Optional[int],
) -> WorkflowResult:
    """Build the workflow result when only already known or rejected PDFs remain."""
    skipped_details = [issue.as_detail() for issue in initial_issues]
    skip_report_path = write_rewe_skipped_receipts_report(pdf_dir, skipped_details)
    print_rewe_skipped_receipts(skipped_details, skip_report_path)
    return WorkflowResult(
        success=True,
        summary=WorkflowSummary(
            retailer=retailer,
            processed_count=0,
            skipped_count=len(initial_issues),
            total_receipts=existing_total_receipts or 0,
            receipts_file=receipts_file,
            total_items=0,
        ),
        skipped_issues=list(initial_issues),
        skipped_report_path=skip_report_path,
    )


def _prepare_rewe_import_session(
        customer_id: Optional[str],
        browser: Optional[str],
        cookies_file: Optional[str],
        output_dir: str,
) -> Optional[tuple[requests.Session, Optional[str]]]:
    """Load the REWE session and resolve the customer id for the initial import."""
    session = _load_rewe_session(
        browser=browser,
        cookies_file=cookies_file,
    )
    if not session:
        return None

    resolved_customer_id = resolve_rewe_customer_id(
        customer_id,
        session,
        cookies_file,
        output_dir,
    )
    print_rewe_session_test_start()
    if not test_rewe_session(session, resolved_customer_id):
        return None
    print_rewe_session_test_success()
    return session, resolved_customer_id


def _download_and_extract_rewe_zip(
        session: requests.Session,
        customer_id: Optional[str],
        zip_path: Path,
        pdf_output_dir: Path,
) -> bool:
    """Download the REWE ZIP and extract the PDFs locally."""
    downloaded_zip = download_receipts_zip(
        session,
        customer_id,
        zip_path,
    )
    if not downloaded_zip:
        return False
    print_rewe_zip_saved(downloaded_zip)
    _extract_rewe_receipts_zip(downloaded_zip, pdf_output_dir)
    return True


def _load_rewe_session(browser: Optional[str], cookies_file: Optional[str]):
    """Authenticate a REWE session for workflow execution."""
    if browser:
        auth_method = browser
    elif cookies_file:
        auth_method = "file"
    else:
        print_rewe_missing_auth_source()
        return None

    return setup_session(
        retailer=RETAILER_REWE,
        auth_method=auth_method,
        cookies_file=cookies_file,
    )


def _extract_rewe_receipts_zip(zip_path: Path, output_dir: Path) -> Path:
    """Extract a downloaded REWE receipts ZIP archive."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(output_dir)
    print_rewe_zip_extracted(output_dir)
    return output_dir
