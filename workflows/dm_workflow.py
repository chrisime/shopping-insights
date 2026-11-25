"""Central dm workflow for purchase-history sync and eBon import.

dm authenticates through OAuth 2.0 PKCE (see :mod:`auth.dm_auth`), so the
workflow first mints a short-lived access token, then fetches the paginated
purchase history, downloads the Market eBon details (JSON) and original PDFs,
and imports them through the shared :func:`local_import.import_local_sources`
path. Online orders are recognized and counted but not persisted.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Callable

import simplejson

from auth.dm_auth import (
    DmAuthError,
    build_dm_api_session,
    make_dm_token_refresher,
)
from auth.session_manager import setup_session
from client.dm_client import (
    collect_dm_purchases,
    download_ebon_pdf,
    fetch_ebon_detail,
    test_dm_session,
)
from config import DmConfig
from config import storage_config
from parsing.dm_ebons_parser import enrich_dm_item_names
from parsing.dm_pdf_items_extractor import extract_dm_pdf_items
from shared.receipt_dates import api_purchase_date
from shared.receipt_store import ReceiptStore
from storage import create_receipt_store

from .import_workflow import ImportWorkflow, resolve_auth_method
from .local_import import import_local_sources
from .pipeline_types import WorkflowResult
from .progress_display import ReceiptProgressDisplay
from .workflow_constants import RETAILER_DM, REASON_KIND_DM_FETCH
from .workflow_errors import clear_last_workflow_error, dm_initial_error, set_last_workflow_error

__all__ = [
    "run_dm_initial",
    "run_dm_update",
]


PURCHASE_TYPE_MARKET = "MARKET"


def _load_dm_ebon_payload(source_path: Path) -> Any:
    """Load one local eBon JSON file into the raw eBon detail dict."""
    data = simplejson.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Ungültiges dm-eBon-Format: erwartetes JSON-Objekt")
    return data


def _is_market_ebon(purchase: dict) -> bool:
    """Return True when the purchase history entry is a Market eBon."""
    return (
        purchase.get("purchaseType") == PURCHASE_TYPE_MARKET
        and purchase.get("ebonData") is not None
    )


class _DmImportWorkflow(ImportWorkflow):
    """Concrete dm workflow: OAuth token + purchase download followed by import."""

    def __init__(self, browser: str | None, cookies_file: str | None) -> None:
        self._browser = browser
        self._cookies_file = cookies_file
        self._online_order_count = 0

    def _source_subdir_name(self) -> str:
        return "ebons"

    def _download_sources(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
        *,
        purchased_since: date | None = None,
    ) -> bool:
        session_payload = _prepare_dm_session(self._browser, self._cookies_file)
        if not session_payload:
            return False
        api_session, token_refresher = session_payload

        ebons_dir = self._source_dir(output_dir)
        ebons_dir.mkdir(parents=True, exist_ok=True)

        print("ℹ Sammle dm-Kaufhistorie...")
        purchases = collect_dm_purchases(api_session, token_refresher=token_refresher, purchased_since=purchased_since)
        if not purchases:
            print("ℹ Keine dm-Kaufhistorie-Einträge gefunden.")
            return True

        market_ebons = [p for p in purchases if _is_market_ebon(p)]
        self._online_order_count = len(purchases) - len(market_ebons)

        print(f"ℹ Gefunden: {len(purchases)} dm-Käufe "
              f"({len(market_ebons)} Markt-eBons, {self._online_order_count} Online-Bestellungen)")
        if self._online_order_count:
            print("ℹ Online-Bestellungen werden nicht als Beleg importiert.")

        existing_ids = store.find_existing_ids(retailer=RETAILER_DM)
        local_ids = {path.stem for path in ebons_dir.glob("*.json")}
        new_ebons = [p for p in market_ebons if p.get("id") not in existing_ids and p.get("id") not in local_ids]

        print(f"ℹ Bereits vorhandene dm-eBons: {len(existing_ids)}")
        print(f"ℹ Neue dm-eBons zu verarbeiten: {len(new_ebons)}")

        if new_ebons:
            _download_dm_ebons(
                api_session,
                new_ebons,
                ebons_dir,
                output_dir,
                token_refresher,
                progress_listener=progress_listener,
                purchased_since=purchased_since,
            )
        return True

    def _validate_update_preconditions(self, output_dir: Path) -> bool:
        ebons_dir = self._source_dir(output_dir)
        if not ebons_dir.exists() or not any(ebons_dir.glob("*.json")):
            print(f"\u26a0 Keine dm-eBon-JSONs zum Importieren gefunden in: {ebons_dir}")
            return False
        return True

    def _run_local_import(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
        *,
        purchased_since: date | None = None,
    ) -> WorkflowResult:
        ebons_dir = self._source_dir(output_dir)
        return import_local_sources(
            source_paths=sorted(ebons_dir.glob("*.json")),
            source_dir=ebons_dir,
            retailer=RETAILER_DM,
            receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
            store=store,
            loader=_load_dm_ebon_payload,
            detail_key="receipt_id",
            load_error_reason_kind=REASON_KIND_DM_FETCH,
            retailer_display_name="dm",
            skipped_report_filename=DmConfig.SKIPPED_RECEIPTS_REPORT_FILE,
            progress_listener=progress_listener,
            purchased_since=purchased_since,
        )

    def _import_summary_label(self) -> str:
        return "dm-eBons importiert"

    def _print_import_summary_details(self, result: WorkflowResult) -> None:
        print(f"ℹ Verarbeitete Artikel: {result.summary.total_items}")
        if self._online_order_count:
            print(f"ℹ Online-Bestellungen (nicht importiert): {self._online_order_count}")

    def _print_no_download_info(self) -> None:
        print("ℹ dm: importiere alle vorhandenen eBon-JSONs.")


def run_dm_initial(
    browser: str | None = None,
    cookies_file: str | None = None,
    output_dir: str = DmConfig.DEFAULT_OUTPUT_DIR,
    progress_listener: Callable[[object], None] | None = None,
    *,
    purchased_since: date | None = None,
) -> bool:
    """Download new dm eBon JSONs and import them into the DB."""
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    workflow = _DmImportWorkflow(browser, cookies_file)
    return workflow.run_initial(
        base_output_dir,
        store,
        progress_listener=progress_listener,
        purchased_since=purchased_since,
    )


def run_dm_update(
    output_dir: str = DmConfig.DEFAULT_OUTPUT_DIR,
    progress_listener: Callable[[object], None] | None = None,
) -> bool:
    """Re-import all locally downloaded dm eBon JSONs via upsert."""
    base_output_dir = Path(output_dir)
    store = create_receipt_store()
    return _DmImportWorkflow(None, None).run_update(
        base_output_dir,
        store,
        progress_listener=progress_listener,
    )


def _prepare_dm_session(
    browser: str | None,
    cookies_file: str | None,
):
    """Mint a dm access token and return an API session plus a token refresher."""
    auth_method = resolve_auth_method(browser, cookies_file, "dm")
    if not auth_method:
        info = dm_initial_error(2301)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None

    cookie_session = setup_session(RETAILER_DM, auth_method, cookies_file)
    if not cookie_session:
        error_code = 2302 if auth_method == "file" else 2303
        info = dm_initial_error(error_code)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None

    try:
        api_session = build_dm_api_session(cookie_session)
    except DmAuthError as exc:
        info = dm_initial_error(2304)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}: {exc}")
        return None

    token_refresher = make_dm_token_refresher(cookie_session)

    print("Teste dm-Session...")
    if not test_dm_session(api_session, token_refresher=token_refresher):
        info = dm_initial_error(2306)
        set_last_workflow_error(info)
        print(f"\u2717 {info.detail}")
        return None
    print("\u2713 dm-Session erfolgreich getestet")
    clear_last_workflow_error()
    return api_session, token_refresher


def _download_dm_ebons(
    api_session,
    new_ebons: list[dict],
    ebons_dir: Path,
    output_dir: Path,
    token_refresher: Callable[[], str | None],
    progress_listener: Callable[[object], None] | None = None,
    *,
    purchased_since: date | None = None,
) -> None:
    """Download dm eBon detail JSONs and PDFs for the given purchases."""
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    saved_count = 0
    error_count = 0

    total_receipts = len(new_ebons)
    progress = ReceiptProgressDisplay.start_download(total_receipts, progress_listener)

    for index, purchase in enumerate(new_ebons, start=1):
        ebon_id = str(purchase.get("id") or "")
        progress.render_step(
            index - 1, total_receipts, saved_count, error_count, 0, ebon_id
        )
        detail = fetch_ebon_detail(api_session, ebon_id, token_refresher=token_refresher)
        if detail is None:
            error_count += 1
            print(f"\u2717 dm-eBon-Detail fehlgeschlagen: {ebon_id}")
        elif (
            purchased_since is None
            or (purchase_date := api_purchase_date(detail.get("date"))) is None
            or purchase_date >= purchased_since
        ):
            if detail.get("hasDownloadableReceipt"):
                pdf_path = pdf_dir / f"{ebon_id}.pdf"
                if download_ebon_pdf(
                    api_session,
                    ebon_id,
                    pdf_path,
                    token_refresher=token_refresher,
                ):
                    pdf_items = extract_dm_pdf_items(pdf_path)
                    if pdf_items:
                        detail["pdfItems"] = pdf_items

            if not detail.get("pdfItems"):
                enrich_dm_item_names(detail.get("bonItems") or [], session=api_session)

            ebon_path = ebons_dir / f"{ebon_id}.json"
            ebon_path.write_text(
                simplejson.dumps(detail, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            saved_count += 1

        progress.render_step(
            index, total_receipts, saved_count, error_count, 0, ebon_id
        )

    progress.close()
    print(f"\u2713 {saved_count} dm-eBon-JSONs gespeichert nach: {ebons_dir}")
    if error_count:
        print(f"\u2717 {error_count} dm-eBon-Details fehlgeschlagen.")