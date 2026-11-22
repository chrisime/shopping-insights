"""Central Rossmann workflow for anybill digital-receipt sync and import.

Rossmann serves digital receipts through the white-label provider anybill.
This workflow mints a short-lived anybill token from the Rossmann account API
(``auth.rossmann_auth``), fetches the paginated receipt list plus details/PDFs
from the anybill App API v4, and imports them through the shared
:func:`local_import.import_local_sources` path (ADR-0003).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import requests
import simplejson

from auth.rossmann_auth import (
    RossmannAccount,
    RossmannAuthError,
    build_anybill_api_session,
    make_anybill_token_refresher,
    mint_anybill_token,
    prompt_rossmann_login,
)
from auth.rossmann_file_auth import read_rossmann_account
from auth.session_manager import setup_session
from client.rossmann_client import (
    collect_rossmann_receipts,
    download_receipt_pdf,
    fetch_receipt_detail,
    test_rossmann_session,
)
from config import RossmannConfig
from config import storage_config
from shared.receipt_store import ReceiptStore
from storage import create_receipt_store

from .import_workflow import ImportWorkflow, resolve_auth_method
from .local_import import import_local_sources
from .pipeline_types import WorkflowResult
from .progress_display import ReceiptProgressDisplay
from .workflow_constants import RETAILER_ROSSMANN, REASON_KIND_ROSSMANN_FETCH
from .workflow_errors import clear_last_workflow_error, rossmann_initial_error, set_last_workflow_error

__all__ = [
    "run_rossmann_initial",
    "run_rossmann_update",
]


def _load_rossmann_receipt_payload(source_path: Path) -> Any:
    """Load one local receipt JSON file into the raw anybill detail dict."""
    data = simplejson.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Ungültiges Rossmann-Belegformat: erwartetes JSON-Objekt")
    return data


class _RossmannImportWorkflow(ImportWorkflow):
    """Concrete Rossmann workflow: token mint + receipt download followed by import."""

    def __init__(
        self,
        browser: str | None,
        cookies_file: str | None,
        account: RossmannAccount | None = None,
    ) -> None:
        self._browser = browser
        self._cookies_file = cookies_file
        self._account = account
        self._pending_receipt_ids: set[str] | None = None
        self._existing_receipt_count = 0

    def _source_subdir_name(self) -> str:
        return "receipts"

    def _download_sources(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> bool:
        session_payload = _prepare_rossmann_session(
            self._browser, self._cookies_file, self._account
        )
        if not session_payload:
            return False
        api_session, token_refresher = session_payload

        receipts_dir = self._source_dir(output_dir)
        receipts_dir.mkdir(parents=True, exist_ok=True)

        print("ℹ Sammle Rossmann-Belege (anybill)...")
        receipts = collect_rossmann_receipts(api_session, token_refresher=token_refresher)
        if receipts is None:
            info = rossmann_initial_error(2406)
            set_last_workflow_error(info)
            print(f"✗ {info.detail}")
            return False

        print(f"ℹ Gefunden: {len(receipts)} Rossmann-Belege")

        existing_ids = store.find_existing_ids(retailer=RETAILER_ROSSMANN)
        self._existing_receipt_count = len(existing_ids)
        self._pending_receipt_ids = {receipt["id"] for receipt in receipts if receipt.get("id")} - existing_ids
        local_ids = {path.stem for path in receipts_dir.glob("*.json")}
        new_receipts = [
            r for r in receipts
            if r.get("id") in self._pending_receipt_ids and r.get("id") not in local_ids
        ]

        print(f"ℹ Bereits vorhandene Rossmann-Belege: {len(existing_ids)}")
        print(f"ℹ Neue Rossmann-Belege zu verarbeiten: {len(new_receipts)}")

        if new_receipts:
            downloaded = _download_rossmann_receipts(
                api_session,
                new_receipts,
                receipts_dir,
                output_dir,
                token_refresher,
                progress_listener=progress_listener,
            )
            if not downloaded:
                set_last_workflow_error(rossmann_initial_error(2408))
                return False
        return True

    def _validate_update_preconditions(self, output_dir: Path) -> bool:
        receipts_dir = self._source_dir(output_dir)
        if not receipts_dir.exists() or not any(receipts_dir.glob("*.json")):
            print(f"\u26a0 Keine Rossmann-Beleg-JSONs zum Importieren gefunden in: {receipts_dir}")
            return False
        return True

    def _run_local_import(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> WorkflowResult:
        receipts_dir = self._source_dir(output_dir)
        source_paths = sorted(
            path for path in receipts_dir.glob("*.json")
            if self._pending_receipt_ids is None or path.stem in self._pending_receipt_ids
        )
        result = import_local_sources(
            source_paths=source_paths,
            source_dir=receipts_dir,
            retailer=RETAILER_ROSSMANN,
            receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
            store=store,
            loader=_load_rossmann_receipt_payload,
            detail_key="receipt_id",
            load_error_reason_kind=REASON_KIND_ROSSMANN_FETCH,
            retailer_display_name="ROSSMANN",
            skipped_report_filename=RossmannConfig.SKIPPED_RECEIPTS_REPORT_FILE,
            progress_listener=progress_listener,
        )
        if not source_paths:
            return replace(result, summary=replace(result.summary, total_receipts=self._existing_receipt_count))
        return result

    def _import_summary_label(self) -> str:
        return "Rossmann-Belege importiert"

    def _print_import_summary_details(self, result: WorkflowResult) -> None:
        print(f"ℹ Verarbeitete Artikel: {result.summary.total_items}")

    def _print_no_download_info(self) -> None:
        print("ℹ Rossmann: importiere alle vorhandenen Beleg-JSONs.")


def run_rossmann_initial(
    browser: str | None = None,
    cookies_file: str | None = None,
    account_id: str | None = None,
    account_hash: str | None = None,
    output_dir: str = RossmannConfig.DEFAULT_OUTPUT_DIR,
    prompt_login: bool = False,
    progress_listener: Callable[[object], None] | None = None,
) -> bool:
    """Download new Rossmann receipt JSONs and import them into the DB."""
    account = _build_account(account_id, account_hash, cookies_file)
    if account is None and prompt_login:
        account = prompt_rossmann_login()
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    return _RossmannImportWorkflow(browser, cookies_file, account).run_initial(
        base_output_dir,
        store,
        progress_listener=progress_listener,
    )


def run_rossmann_update(
    output_dir: str = RossmannConfig.DEFAULT_OUTPUT_DIR,
    progress_listener: Callable[[object], None] | None = None,
) -> bool:
    """Re-import all locally downloaded Rossmann receipt JSONs via upsert."""
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    return _RossmannImportWorkflow(None, None).run_update(
        base_output_dir,
        store,
        progress_listener=progress_listener,
    )


def _build_account(
    account_id: str | None,
    account_hash: str | None,
    cookies_file: str | None,
) -> RossmannAccount | None:
    """Resolve the Rossmann account from CLI args or an embedded cookie export."""
    if account_id and account_hash:
        return RossmannAccount(account_id=account_id, account_hash=account_hash)

    if cookies_file:
        try:
            raw = Path(cookies_file).read_text(encoding="utf-8")
        except OSError:
            return None
        account = read_rossmann_account(raw)
        if account:
            return RossmannAccount(
                account_id=account["accountId"],
                account_hash=account["accountHash"],
            )

    return None


def _prepare_rossmann_session(
    browser: str | None,
    cookies_file: str | None,
    account: RossmannAccount | None,
):
    """Mint an anybill token and return an API session plus a token refresher."""
    if account is not None and browser is None and cookies_file is None:
        account_session = requests.Session()
        account_session.headers["User-Agent"] = RossmannConfig.DEFAULT_USER_AGENT
    else:
        auth_method = resolve_auth_method(browser, cookies_file, "Rossmann")
        if not auth_method:
            set_last_workflow_error(rossmann_initial_error(2401))
            return None

        account_session = setup_session(RETAILER_ROSSMANN, auth_method, cookies_file)
        if not account_session:
            error_code = 2402 if auth_method == "file" else 2403
            info = rossmann_initial_error(error_code)
            set_last_workflow_error(info)
            print(f"\u2717 {info.detail}")
            return None

    if account is None:
        info = rossmann_initial_error(2405)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail} (accountId/accountHash erforderlich)")
        return None

    try:
        api_session = build_anybill_api_session(account_session, account)
    except RossmannAuthError as exc:
        info = rossmann_initial_error(2404)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}: {exc}")
        return None

    token_refresher = make_anybill_token_refresher(account_session, account)

    print("Teste Rossmann/anybill-Session...")
    if not _test_rossmann_client_session(api_session, token_refresher):
        info = rossmann_initial_error(2406)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None
    print("\u2713 Rossmann/anybill-Session erfolgreich getestet")
    clear_last_workflow_error()
    return api_session, token_refresher


def _test_rossmann_client_session(api_session, token_refresher) -> bool:
    from client.rossmann_client import test_rossmann_session

    return test_rossmann_session(api_session, token_refresher=token_refresher)


def _download_rossmann_receipts(
    api_session,
    new_receipts: list[dict],
    receipts_dir: Path,
    output_dir: Path,
    token_refresher: Callable[[], str | None],
    progress_listener: Callable[[object], None] | None = None,
) -> bool:
    """Download Rossmann receipt detail JSONs and PDFs for the list entries."""
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    saved_count = 0
    error_count = 0

    progress = ReceiptProgressDisplay(
        added_label="Gespeichert",
        items_label="Artikel",
        listener=progress_listener,
    )
    total_receipts = len(new_receipts)
    progress.render_step(0, total_receipts, 0, 0, 0, "-")

    for index, entry in enumerate(new_receipts, start=1):
        receipt_id = str(entry.get("id") or "")
        progress.render_step(
            index - 1, total_receipts, saved_count, error_count, 0, receipt_id
        )
        detail = fetch_receipt_detail(api_session, receipt_id, token_refresher=token_refresher)
        if detail is None:
            error_count += 1
            print(f"\u2717 Rossmann-Detail fehlgeschlagen: {receipt_id}")
        else:
            ebon_path = receipts_dir / f"{receipt_id}.json"
            ebon_path.write_text(
                simplejson.dumps(detail, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            saved_count += 1

            pdf_path = pdf_dir / f"{receipt_id}.pdf"
            download_receipt_pdf(
                api_session,
                receipt_id,
                pdf_path,
                token_refresher=token_refresher,
            )

        progress.render_step(
            index, total_receipts, saved_count, error_count, 0, receipt_id
        )

    progress.close()
    print(f"\u2713 {saved_count} Rossmann-Beleg-JSONs gespeichert nach: {receipts_dir}")
    if error_count:
        print(f"\u2717 {error_count} Rossmann-Details fehlgeschlagen.")
    return error_count == 0
