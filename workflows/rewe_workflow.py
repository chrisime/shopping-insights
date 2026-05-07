"""Central REWE workflows for eBon download, PDF import and diagnostics."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple
import zipfile

from api.rewe_client import download_receipts_zip, test_rewe_session
from auth.rewe_customer_id import cache_customer_id, resolve_rewe_customer_id
from auth.rewe_file_auth import diagnose_rewe_cookie_file
from auth.session_manager import setup_session
from parsing.rewe_pdf_parser import extract_rewe_receipt_metadata_from_pdf
from parsing.rewe_pdf_parser import parse_rewe_receipt_pdf
from parsing.rewe_validator import ReweReceiptValidationError, validate_rewe_receipt_data
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
from result_types import ReceiptParseResult, WorkflowSummary
from shared.ports import ReceiptStore
from storage import create_receipt_store

from .error_mapping import (
    build_exception_issue,
    build_exception_skip_result,
    build_receipt_issue,
    build_validation_skip_result,
)
from .progress_display import ProgressState, ReceiptProgressDisplay
from .pipeline_runner import parse_receipts, persist_valid_receipts, validate_receipts
from .pipeline_types import RawReceiptRecord, ReceiptIssue, WorkflowResult

REWE_DEFAULT_OUTPUT_DIR = "tmp/rewe"

__all__ = [
    "run_rewe_initial",
    "run_rewe_update",
    "run_rewe_check",
    "import_rewe_receipts_from_pdfs",
    "parse_rewe_receipt_pdf_with_result",
]


@dataclass(frozen=True)
class ReweImportContext:
    """Prepared REWE import context for the initial online ZIP workflow."""

    session: object
    customer_id: Optional[str]
    output_dir: Path
    zip_path: Path
    pdf_output_dir: Path


# ---------------------------------------------------------------------------
# Public use cases
# ---------------------------------------------------------------------------


def run_rewe_initial(
        customer_id: Optional[str] = None,
        browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        output_dir: str = REWE_DEFAULT_OUTPUT_DIR,
        write_backend: str = "json",
) -> bool:
    """Run the full REWE eBon workflow: download ZIP, extract PDFs, import JSON."""
    return _run_rewe_initial_import(
        customer_id=customer_id,
        browser=browser,
        cookies_file=cookies_file,
        output_dir=output_dir,
        write_backend=write_backend,
    )


def run_rewe_update(
        customer_id: Optional[str] = None,
        browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        output_dir: str = REWE_DEFAULT_OUTPUT_DIR,
        write_backend: str = "json",
) -> bool:
    """Run the local REWE update workflow on already downloaded PDFs."""
    _ = customer_id, browser, cookies_file
    print_rewe_update_no_delta()
    store = create_receipt_store(write_backend)
    pdf_output_dir = Path(output_dir) / "pdfs"
    snapshot = store.load_receipts_snapshot(retailer="rewe")
    pdf_paths = sorted(pdf_output_dir.glob("*.pdf"))

    if not pdf_paths:
        workflow_result = _run_rewe_pdf_import_pipeline(
            pdf_output_dir,
            retailer="rewe",
            store=store,
            receipts_file=snapshot.receipts_file,
        )
    else:
        new_pdf_paths, prefilter_issues = _filter_new_rewe_pdf_paths(
            pdf_paths,
            snapshot.existing_ids,
        )
        workflow_result = _run_rewe_pdf_import_pipeline(
            pdf_output_dir,
            retailer="rewe",
            store=store,
            pdf_paths=new_pdf_paths,
            prefilter_issues=prefilter_issues,
            existing_total_receipts=len(snapshot.receipts),
            receipts_file=snapshot.receipts_file,
        )

    print_rewe_import_summary(workflow_result.summary)
    return workflow_result.success


# ---------------------------------------------------------------------------
# Public diagnostics / import helpers
# ---------------------------------------------------------------------------


def run_rewe_check(cookies_file: Optional[str] = None) -> bool:
    """Validate a REWE cookie/request file."""
    return diagnose_rewe_cookie_file(cookies_file)


def import_rewe_receipts_from_pdfs(
        pdf_dir: Path,
        file_path: Optional[str] = None,
        retailer: str = "rewe",
        write_backend: str = "json",
) -> Tuple[int, int, int]:
    """Parse, validate and persist extracted REWE PDFs via the configured store."""
    store = create_receipt_store(write_backend)
    snapshot = store.load_receipts_snapshot(file_path=file_path, retailer=retailer)
    workflow_result = _run_rewe_pdf_import_pipeline(
        pdf_dir,
        file_path=file_path,
        retailer=retailer,
        store=store,
        receipts_file=snapshot.receipts_file,
    )
    return (
        workflow_result.summary.processed_count,
        workflow_result.summary.skipped_count,
        workflow_result.summary.total_receipts,
    )


def parse_rewe_receipt_pdf_with_result(pdf_path) -> ReceiptParseResult:
    """Parse and validate a single REWE PDF inside the workflow layer."""
    return _parse_rewe_receipt_pdf_with_result(pdf_path)


# ---------------------------------------------------------------------------
# Pipeline assembly helpers
# ---------------------------------------------------------------------------


def _run_rewe_initial_import(
        customer_id: Optional[str],
        browser: Optional[str],
        cookies_file: Optional[str],
        output_dir: str,
        write_backend: str,
) -> bool:
    """Run the shared REWE import pipeline used by the initial import."""
    store = create_receipt_store(write_backend)
    import_context = _prepare_rewe_import_context(
        customer_id=customer_id,
        browser=browser,
        cookies_file=cookies_file,
        output_dir=output_dir,
    )
    if not import_context:
        return False

    if not _download_and_extract_rewe_zip(import_context):
        return False

    workflow_result = _run_rewe_pdf_import_pipeline(
        import_context.pdf_output_dir,
        retailer="rewe",
        store=store,
        receipts_file=store.load_receipts_snapshot(retailer="rewe").receipts_file,
    )
    print_rewe_import_summary(workflow_result.summary)

    if import_context.customer_id:
        cache_customer_id(import_context.customer_id, str(import_context.output_dir))
    return workflow_result.success


def _run_rewe_pdf_import_pipeline(
        pdf_dir: Path,
        store: ReceiptStore,
        receipts_file: str,
        file_path: Optional[str] = None,
        retailer: str = "rewe",
        pdf_paths: Optional[Sequence[Path]] = None,
        prefilter_issues: Optional[Sequence[ReceiptIssue]] = None,
        existing_total_receipts: Optional[int] = None,
) -> WorkflowResult:
    """Parse, validate and persist extracted REWE PDFs and return a normalized workflow result."""
    active_pdf_paths = list(pdf_paths) if pdf_paths is not None else sorted(pdf_dir.glob("*.pdf"))
    initial_issues = list(prefilter_issues or [])
    if not active_pdf_paths:
        if pdf_paths is None:
            return _build_rewe_missing_pdfs_result(
                pdf_dir=pdf_dir,
                receipts_file=receipts_file,
                retailer=retailer,
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
        parse_record=lambda raw_record: parse_rewe_receipt_pdf(raw_record.payload),
        detail_key="file",
        unexpected_error_formatter=_format_rewe_pdf_parse_error,
    )
    validation_result = validate_receipts(
        parse_result.records,
        validate_receipt=validate_rewe_receipt_data,
        validation_error_types=(ReweReceiptValidationError,),
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


def _build_rewe_missing_pdfs_result(
    pdf_dir: Path,
    receipts_file: str,
    retailer: str,
) -> WorkflowResult:
    """Build the workflow result for the case that no local REWE PDFs exist at all."""
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


def _filter_new_rewe_pdf_paths(
        pdf_paths: Sequence[Path],
        existing_ids: Sequence[str],
) -> tuple[list[Path], list[ReceiptIssue]]:
    """Return only REWE PDFs whose extracted receipt ids are not already stored."""
    known_ids = set(existing_ids)
    new_pdf_paths: list[Path] = []
    issues: list[ReceiptIssue] = []
    known_pdf_count = 0
    progress = ReceiptProgressDisplay(
        added_label="Neu",
        skipped_label="Bekannt",
        errors_label="Fehler",
        items_label="Erkannt",
    )
    total_pdfs = len(pdf_paths)

    progress.render(ProgressState(0, total_pdfs, 0, 0, 0, 0, "-"))

    for index, pdf_path in enumerate(pdf_paths, 1):
        progress.render(
            _build_rewe_delta_scan_state(
                current=index - 1,
                total=total_pdfs,
                new_pdf_paths=new_pdf_paths,
                known_pdf_count=known_pdf_count,
                issues=issues,
                current_receipt=pdf_path.name,
            )
        )
        try:
            metadata = extract_rewe_receipt_metadata_from_pdf(pdf_path)
        except Exception as exc:  # pragma: no cover - defensive fallback
            issues.append(
                build_exception_issue(
                    source_id=pdf_path.name,
                    detail_key="file",
                    exc=exc,
                    reason_formatter=_format_rewe_delta_scan_error,
                )
            )
            progress.render(
                _build_rewe_delta_scan_state(
                    current=index,
                    total=total_pdfs,
                    new_pdf_paths=new_pdf_paths,
                    known_pdf_count=known_pdf_count,
                    issues=issues,
                    current_receipt=pdf_path.name,
                )
            )
            continue

        receipt_id = metadata.get("id")
        if not receipt_id:
            issues.append(
                build_receipt_issue(
                    source_id=pdf_path.name,
                    reason="Bon konnte nicht für Delta-Prüfung identifiziert werden: fehlende REWE-ID",
                    detail_key="file",
                )
            )
            progress.render(
                _build_rewe_delta_scan_state(
                    current=index,
                    total=total_pdfs,
                    new_pdf_paths=new_pdf_paths,
                    known_pdf_count=known_pdf_count,
                    issues=issues,
                    current_receipt=pdf_path.name,
                )
            )
            continue

        if receipt_id in known_ids:
            known_pdf_count += 1
            progress.render(
                _build_rewe_delta_scan_state(
                    current=index,
                    total=total_pdfs,
                    new_pdf_paths=new_pdf_paths,
                    known_pdf_count=known_pdf_count,
                    issues=issues,
                    current_receipt=pdf_path.name,
                )
            )
            continue

        known_ids.add(receipt_id)
        new_pdf_paths.append(pdf_path)

        progress.render(
            _build_rewe_delta_scan_state(
                current=index,
                total=total_pdfs,
                new_pdf_paths=new_pdf_paths,
                known_pdf_count=known_pdf_count,
                issues=issues,
                current_receipt=pdf_path.name,
            )
        )

    progress.close()
    return new_pdf_paths, issues


# ---------------------------------------------------------------------------
# Single-receipt / delta-scan helpers
# ---------------------------------------------------------------------------


def _build_rewe_delta_scan_state(
    current: int,
    total: int,
    new_pdf_paths: Sequence[Path],
    known_pdf_count: int,
    issues: Sequence[ReceiptIssue],
    current_receipt: str,
) -> ProgressState:
    """Create a consistent progress snapshot for the REWE local delta scan."""
    return ProgressState(
        current=current,
        total=total,
        added=len(new_pdf_paths),
        skipped=known_pdf_count,
        errors=len(issues),
        items=len(new_pdf_paths) + known_pdf_count,
        current_receipt=current_receipt,
    )


def _parse_rewe_receipt_pdf_with_result(pdf_path) -> ReceiptParseResult:
    """Parse and validate a single REWE PDF inside the workflow layer."""
    path = Path(pdf_path)
    try:
        receipt_data = parse_rewe_receipt_pdf(path)
        validate_rewe_receipt_data(receipt_data)
        return ReceiptParseResult(receipt_data=receipt_data)
    except ReweReceiptValidationError as exc:
        return build_validation_skip_result(exc)
    except ValueError as exc:
        return build_exception_skip_result(exc)
    except Exception as exc:  # pragma: no cover - filesystem/pdfplumber dependent
        return build_exception_skip_result(exc, reason_formatter=_format_rewe_pdf_parse_error)


# ---------------------------------------------------------------------------
# Session / setup helpers
# ---------------------------------------------------------------------------


def _prepare_rewe_import_context(
    customer_id: Optional[str],
    browser: Optional[str],
    cookies_file: Optional[str],
    output_dir: str,
) -> Optional[ReweImportContext]:
    """Load the REWE session, resolve the customer id and assemble the initial import context."""
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

    base_output_dir = Path(output_dir)
    return ReweImportContext(
        session=session,
        customer_id=resolved_customer_id,
        output_dir=base_output_dir,
        zip_path=base_output_dir / "receipts.zip",
        pdf_output_dir=base_output_dir / "pdfs",
    )


def _download_and_extract_rewe_zip(import_context: ReweImportContext) -> bool:
    """Download the REWE ZIP for the prepared context and extract the PDFs locally."""
    downloaded_zip = download_receipts_zip(
        import_context.session,
        import_context.customer_id,
        import_context.zip_path,
    )
    if not downloaded_zip:
        return False
    print_rewe_zip_saved(downloaded_zip)
    _extract_rewe_receipts_zip(downloaded_zip, import_context.pdf_output_dir)
    return True


def _load_rewe_session(
        browser: Optional[str],
        cookies_file: Optional[str],
):
    """Authenticate a REWE session for workflow execution."""
    if browser:
        auth_method = browser
    elif cookies_file:
        auth_method = "file"
    else:
        print_rewe_missing_auth_source()
        return None

    return setup_session(
        retailer="rewe",
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


def _format_rewe_pdf_parse_error(exc: Exception) -> str:
    """Render REWE PDF parse exceptions into stable workflow reason strings."""
    return f"PDF konnte nicht gelesen werden: {exc}"


def _format_rewe_delta_scan_error(exc: Exception) -> str:
    """Render REWE local delta-scan exceptions into stable workflow reason strings."""
    return f"Bon konnte nicht für Delta-Prüfung identifiziert werden: {exc}"

