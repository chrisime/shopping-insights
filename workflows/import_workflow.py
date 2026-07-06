"""Abstract base for workflows that combine a download phase with a local file import."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

from reporting.shared_reporting import print_import_summary
from shared.receipt_store import ReceiptStore

from .pipeline_types import WorkflowResult


class ImportWorkflow(ABC):
    """Template-method base for retailer workflows: download → import → summary.

    Concrete subclasses implement the retailer-specific steps; this class
    provides the shared control flow for both the *initial* (download + import)
    and *update* (import-only) modes.
    """

    @abstractmethod
    def _source_subdir_name(self) -> str:
        """Return the local source subdirectory name (e.g. ``tickets`` or ``pdfs``)."""

    def _source_dir(self, output_dir: Path) -> Path:
        """Return the retailer-specific local source directory inside ``output_dir``."""
        return output_dir / self._source_subdir_name()

    @abstractmethod
    def _download_sources(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> bool:
        """Prepare session and download raw source files.

        Return ``False`` to abort the workflow (e.g. authentication failure).
        ``store`` is available for retailers that need to filter already-known
        receipts before downloading.
        """

    @abstractmethod
    def _run_local_import(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> WorkflowResult:
        """Parse, validate and persist all local source files."""

    @abstractmethod
    def _import_summary_label(self) -> str:
        """Return the normalized summary label used for shared import reporting."""

    def _print_import_summary(self, result: WorkflowResult) -> None:
        """Print the shared summary line and optional subclass-specific details."""
        print_import_summary(result.summary, self._import_summary_label())
        self._print_import_summary_details(result)

    def _print_import_summary_details(self, result: WorkflowResult) -> None:
        """Print retailer-specific summary details (default: no-op)."""

    @abstractmethod
    def _print_no_download_info(self) -> None:
        """Print an info message explaining that the update skips the download."""

    def _validate_update_preconditions(self, output_dir: Path) -> bool:
        """Return ``False`` to abort ``run_update`` early (default: always valid)."""
        return True

    def _post_import(self, result: WorkflowResult, output_dir: Path) -> None:
        """Called after a successful initial import (default: no-op)."""

    def run_initial(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> bool:
        """Template: download sources → local import → summary → post-import hook."""
        if not self._download_sources(output_dir, store, progress_listener=progress_listener):
            return False
        result = self._run_local_import(output_dir, store, progress_listener=progress_listener)
        self._print_import_summary(result)
        self._post_import(result, output_dir)
        return result.success

    def run_update(
        self,
        output_dir: Path,
        store: ReceiptStore,
        progress_listener: Callable[[object], None] | None = None,
    ) -> bool:
        """Template: no-download info → precondition check → import → summary."""
        self._print_no_download_info()
        if not self._validate_update_preconditions(output_dir):
            return False
        result = self._run_local_import(output_dir, store, progress_listener=progress_listener)
        self._print_import_summary(result)
        return result.success


def resolve_auth_method(browser: Optional[str], cookies_file: Optional[str], retailer_name: str) -> Optional[str]:
    """Determine the authentication method from CLI arguments."""
    if browser:
        return browser
    if cookies_file:
        return "file"
    print(f"\u2717 {retailer_name} ben\u00f6tigt --cookies-file oder --browser.")
    return None
