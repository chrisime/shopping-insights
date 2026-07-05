"""Central LIDL workflow for synchronizing receipt state from the Lidl API."""

import time
from pathlib import Path
from typing import Any, List, Optional, Sequence

import simplejson
from client.lidl_client import collect_lidl_receipt_ids, get_lidl_ticket, test_lidl_session
from auth.session_manager import setup_session
from config import LidlConfig
from config import storage_config

from requests import Session
from shared.receipt_store import ReceiptStore
from shared.lidl_ticket_dto import LidlTicketDTO
from storage import create_receipt_store
from .import_workflow import ImportWorkflow, resolve_auth_method
from .import_pipeline import ImportPipeline
from .pipeline_types import WorkflowResult
from .progress_display import ReceiptProgressDisplay
from .workflow_constants import RETAILER_LIDL, REASON_KIND_LIDL_FETCH

__all__ = [
    "run_lidl_initial",
    "run_lidl_update",
]


class _LidlImportPipeline(ImportPipeline):
    detail_key = "receipt_id"
    load_error_reason_kind = REASON_KIND_LIDL_FETCH
    retailer_display_name = "LIDL"
    _skipped_report_filename = LidlConfig.SKIPPED_RECEIPTS_REPORT_FILE

    def load_payload(self, source_path: Path) -> Any:
        ticket_data = simplejson.loads(source_path.read_text(encoding="utf-8"))
        receipt_id = source_path.stem
        if isinstance(ticket_data, dict):
            return LidlTicketDTO.from_api_response(ticket_data, receipt_id)
        raise ValueError("Ungültiges LIDL-Ticketformat: erwartetes JSON-Objekt")


class _LidlImportWorkflow(ImportWorkflow):
    """Concrete LIDL workflow: API download of ticket JSONs followed by local import."""

    def __init__(self, browser: Optional[str], cookies_file: Optional[str], country: Optional[str]) -> None:
        self._browser = browser
        self._cookies_file = cookies_file
        self._country = country
        self._checked_pages: Optional[int] = None

    def _source_subdir_name(self) -> str:
        return "tickets"

    def _download_sources(self, output_dir: Path, store: ReceiptStore) -> bool:
        session = _prepare_lidl_session(self._browser, self._cookies_file, self._country)
        if not session:
            return False

        tickets_dir = self._source_dir(output_dir)
        tickets_dir.mkdir(parents=True, exist_ok=True)
        print("ℹ Sammle alle LIDL-Kassenbon-IDs mit digitalem Kassenbon über API...")
        discovered_ids, page_count = collect_lidl_receipt_ids(session)
        self._checked_pages = page_count

        print(f"ℹ Gefunden: {len(discovered_ids)} LIDL-Kassenbon-IDs")
        existing_ids = store.find_existing_ids(retailer=RETAILER_LIDL)
        local_ids = {path.stem for path in tickets_dir.glob("*.json")}
        receipt_ids = _filter_new_lidl_receipt_ids(discovered_ids, existing_ids | local_ids)

        print(f"ℹ Bereits vorhandene Kassenbons: {len(existing_ids)}")
        print(f"ℹ Geprüfte Seiten: {page_count}")
        print(f"ℹ Neue Kassenbons zu verarbeiten: {len(receipt_ids)}")

        if receipt_ids:
            _download_lidl_tickets(session, receipt_ids, tickets_dir)
        return True

    def _validate_update_preconditions(self, output_dir: Path) -> bool:
        tickets_dir = self._source_dir(output_dir)
        if not tickets_dir.exists() or not any(tickets_dir.glob("*.json")):
            print(f"\u26a0 Keine LIDL-JSONs zum Importieren gefunden in: {tickets_dir}")
            return False
        return True

    def _run_local_import(self, output_dir: Path, store: ReceiptStore) -> WorkflowResult:
        tickets_dir = self._source_dir(output_dir)
        return _LidlImportPipeline().run(
            source_paths=sorted(tickets_dir.glob("*.json")),
            source_dir=tickets_dir,
            retailer=RETAILER_LIDL,
            receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
            store=store,
            checked_pages=self._checked_pages,
        )

    def _import_summary_label(self) -> str:
        return "LIDL-Kassenbons importiert"

    def _print_import_summary_details(self, result: WorkflowResult) -> None:
        if self._checked_pages is not None:
            print(f"ℹ Geprüfte Seiten: {self._checked_pages}")
        print(f"ℹ Verarbeitete Artikel: {result.summary.total_items}")

    def _print_no_download_info(self) -> None:
        print("ℹ LIDL: importiere alle vorhandenen JSONs.")


def run_lidl_initial(
    browser: Optional[str] = None,
    cookies_file: Optional[str] = None,
    country: Optional[str] = None,
    output_dir: str = LidlConfig.DEFAULT_OUTPUT_DIR,
) -> bool:
    """Download new Lidl ticket JSONs and import them into the DB."""
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    return _LidlImportWorkflow(browser, cookies_file, country).run_initial(base_output_dir, store)


def run_lidl_update(output_dir: str = LidlConfig.DEFAULT_OUTPUT_DIR) -> bool:
    """Re-import all locally downloaded Lidl JSONs into the configured store via upsert."""
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    return _LidlImportWorkflow(None, None, None).run_update(base_output_dir, store)


def _prepare_lidl_session(browser: Optional[str], cookies_file: Optional[str], country: Optional[str]) -> Optional[Session]:
    """Configure, authenticate and verify the LIDL session."""
    if country:
        LidlConfig.set_country(country)

    auth_method = resolve_auth_method(browser, cookies_file, "LIDL")
    if not auth_method:
        return None

    session = setup_session(RETAILER_LIDL, auth_method, cookies_file)
    if not session:
        return None

    if not _test_lidl_workflow_session(session):
        return None

    return session


def _test_lidl_workflow_session(session: Session) -> bool:
    """Run the workflow-level LIDL session test including reporting side effects."""
    print("ℹ Teste LIDL-Session...")
    if not test_lidl_session(session):
        print(f"✗ API-Verbindungsfehler: LIDL-Session konnte nicht geprüft werden")
        return False
    print("✓ LIDL-Session erfolgreich getestet")
    return True


def _download_lidl_tickets(session: Session, receipt_ids: List[str], tickets_dir: Path) -> None:
    """Download Lidl ticket JSONs and save them to the local tickets directory."""
    progress = ReceiptProgressDisplay(
        added_label="Gespeichert",
        items_label="Artikel",
    )
    total_receipts = len(receipt_ids)
    total_items = 0
    saved_count = 0
    error_count = 0

    progress.render_step(0, total_receipts, 0, 0, 0, "-")

    for index, receipt_id in enumerate(receipt_ids, 1):
        progress.render_step(
            index - 1, total_receipts,
            saved_count, error_count, total_items, receipt_id,
        )
        try:
            ticket_dto = get_lidl_ticket(session, receipt_id)
            ticket_path = tickets_dir / f"{receipt_id}.json"
            ticket_path.write_text(
                simplejson.dumps(ticket_dto.to_api_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            saved_count += 1
        except Exception:
            error_count += 1

        progress.render_step(
            index, total_receipts,
            saved_count, error_count, total_items, receipt_id,
        )
        if LidlConfig.REQUEST_DELAY > 0:
            time.sleep(LidlConfig.REQUEST_DELAY)

    progress.close()
    print(f"✓ {saved_count} Ticket-JSONs gespeichert nach: {tickets_dir}")


def _filter_new_lidl_receipt_ids(discovered_receipt_ids: Sequence[str], existing_receipt_ids: set[str]) -> List[str]:
    """Return only new receipt ids and keep their original discovery order."""
    return [receipt_id for receipt_id in dict.fromkeys(discovered_receipt_ids) if receipt_id not in existing_receipt_ids]
