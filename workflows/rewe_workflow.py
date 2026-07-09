"""Central REWE workflows for eBon download, PDF import and diagnostics."""

import logging
from pathlib import Path
from typing import Callable, Optional
import zipfile

from requests import Session

from client.rewe_client import download_receipts_zip, test_rewe_session
from auth.rewe_browser_auth import ReweBrowserAuthError
from auth.rewe_customer_id import cache_customer_id, resolve_rewe_customer_id
from auth.session_manager import setup_session
from config import storage_config, ReweConfig
from shared.receipt_store import ReceiptStore
from storage import create_receipt_store

from .import_workflow import ImportWorkflow, resolve_auth_method
from .import_pipeline import ImportPipeline
from .pipeline_types import WorkflowResult
from .workflow_constants import RETAILER_REWE, REASON_KIND_REWE_PDF_PARSE
from .workflow_errors import rewe_initial_error, set_last_workflow_error, clear_last_workflow_error, WorkflowErrorInfo


logger = logging.getLogger(__name__)


__all__ = [
    "run_rewe_initial",
    "run_rewe_update",
]


class _ReweImportPipeline(ImportPipeline):
    load_error_reason_kind = REASON_KIND_REWE_PDF_PARSE
    retailer_display_name = "REWE"
    _skipped_report_filename = ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE


class _ReweImportWorkflow(ImportWorkflow):
    """Concrete REWE workflow: ZIP download and PDF extraction followed by local import."""

    def __init__(self, customer_id: Optional[str], browser: Optional[str], cookies_file: Optional[str]) -> None:
        self._customer_id = customer_id
        self._browser = browser
        self._cookies_file = cookies_file
        self._resolved_customer_id: Optional[str] = None

    def _source_subdir_name(self) -> str:
        return "pdfs"

    def _download_sources(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> bool:
        session_and_customer_id = _prepare_rewe_session(self._customer_id, self._browser, self._cookies_file, output_dir)
        if not session_and_customer_id:
            return False
        session, self._resolved_customer_id = session_and_customer_id

        zip_path = output_dir / "receipts.zip"

        target_dir = self._source_dir(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        return _download_and_extract_rewe_zip(session, self._resolved_customer_id, zip_path, target_dir)

    def _run_local_import(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> WorkflowResult:
        return _run_rewe_pdf_import_pipeline(self._source_dir(output_dir), store, progress_listener=progress_listener)

    def _import_summary_label(self) -> str:
        return "REWE-eBons importiert"

    def _print_no_download_info(self) -> None:
        print("ℹ REWE: importiere alle vorhandenen lokalen PDFs.")

    def _validate_update_preconditions(self, output_dir: Path) -> bool:
        pdf_dir = self._source_dir(output_dir)
        if not pdf_dir.exists() or not any(pdf_dir.glob("*.pdf")):
            print(f"\u26a0 Keine REWE-PDFs zum Importieren gefunden in: {pdf_dir}")
            return False
        return True

    def _post_import(self, result: WorkflowResult, output_dir: Path) -> None:
        if self._resolved_customer_id:
            cache_customer_id(self._resolved_customer_id, output_dir)


def run_rewe_initial(
        customer_id: Optional[str] = None,
        browser: Optional[str] = None,
        cookies_file: Optional[str] = None,
        output_dir: str = ReweConfig.REWE_DEFAULT_OUTPUT_DIR,
        progress_listener: Callable[[object], None] | None = None,
) -> bool:
    """Run the full REWE eBon workflow: download ZIP, extract PDFs, import into DB."""
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    return _ReweImportWorkflow(customer_id, browser, cookies_file).run_initial(
        base_output_dir,
        store,
        progress_listener=progress_listener,
    )


def run_rewe_update(
    output_dir: str = ReweConfig.REWE_DEFAULT_OUTPUT_DIR,
    progress_listener: Callable[[object], None] | None = None,
) -> bool:
    """Re-import all locally downloaded REWE PDFs into the configured store via upsert."""
    store = create_receipt_store()
    return _ReweImportWorkflow(None, None, None).run_update(
        Path(output_dir),
        store,
        progress_listener=progress_listener,
    )


def _run_rewe_pdf_import_pipeline(
    pdf_dir: Path,
    store: ReceiptStore,
    progress_listener: Callable[[object], None] | None = None,
) -> WorkflowResult:
    """Parse, validate and persist extracted REWE PDFs and return a normalized workflow result."""
    active_pdf_paths = sorted(pdf_dir.glob("*.pdf"))
    return _ReweImportPipeline().run(
        source_paths=active_pdf_paths,
        source_dir=pdf_dir,
        retailer=RETAILER_REWE,
        receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
        store=store,
        progress_listener=progress_listener,
    )


def _prepare_rewe_session(
        customer_id: Optional[str],
        browser: Optional[str],
        cookies_file: Optional[str],
        output_dir: Path,
) -> Optional[tuple[Session, Optional[str]]]:
    """Load the REWE session and resolve the customer id for the initial import."""
    auth_method = resolve_auth_method(browser, cookies_file, "REWE")
    if not auth_method:
        info = _rewe_initial_error(2201)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None

    try:
        session = setup_session(RETAILER_REWE, auth_method, cookies_file)
    except ReweBrowserAuthError as exc:
        info = _rewe_initial_error(2205, str(exc))
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None

    if not session:
        error_code = 2202 if auth_method == "file" else 2203
        info = _rewe_initial_error(error_code)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None

    resolved_customer_id = resolve_rewe_customer_id(customer_id, session, cookies_file, output_dir)

    print("Teste REWE-Session...")
    if not test_rewe_session(session, resolved_customer_id):
        info = _rewe_initial_error(2207)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None
    print("\u2713 REWE-Session erfolgreich getestet")
    clear_last_workflow_error()
    return session, resolved_customer_id


def _rewe_initial_error(error_code: int, detail: str | None = None) -> WorkflowErrorInfo:
    """Look up the error info for the given code, with optional detail override."""
    info = rewe_initial_error(error_code)
    if error_code == 2205 and detail is not None:
        normalized = detail.lower()
        if "gesperrt" in normalized or "locked" in normalized:
            detail_text = "Browserprofil gesperrt"
        elif "rstp nicht aus browser-session lesbar" in normalized:
            detail_text = "rstp nicht aus Browser-Session lesbar"
        elif "rstp fehlt im browserprofil" in normalized:
            detail_text = "rstp fehlt im Browserprofil"
        elif "cookies liefern" in normalized:
            detail_text = "Browserprofil konnte keine Cookies liefern"
        else:
            detail_text = detail
    else:
        detail_text = detail or info.detail

    return WorkflowErrorInfo(info.retailer, info.error_code, detail_text)


def _download_and_extract_rewe_zip(
        session: Session,
        customer_id: Optional[str],
        zip_path: Path,
        pdf_output_dir: Path,
) -> bool:
    """Download the REWE ZIP and extract the PDFs locally."""
    downloaded_zip = download_receipts_zip(session, customer_id, zip_path)

    if not downloaded_zip:
        error_code = 2208 if customer_id else 2209
        info = _rewe_initial_error(error_code)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return False
    print(f"\u2713 REWE-eBons ZIP gespeichert: {downloaded_zip}")

    with zipfile.ZipFile(downloaded_zip, "r") as archive:
        archive.extractall(pdf_output_dir)
        print(f"\u2713 REWE-eBons entpackt nach: {pdf_output_dir}")

    return True
