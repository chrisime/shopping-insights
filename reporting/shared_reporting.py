"""Shared workflow reporting helpers used by all retailer workflows."""

from __future__ import annotations

import simplejson
from pathlib import Path
from typing import Optional

from result_types import WorkflowSummary


def write_skipped_receipts_report(skipped_details: list[dict[str, str]], report_path: Path) -> Optional[Path]:
    """Write skipped receipts into a JSON report at the given path.

    Returns the resolved path, or ``None`` when there is nothing to report.
    """
    if not skipped_details:
        return None

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "count": len(skipped_details),
        "skipped_receipts": skipped_details,
    }
    report_path.write_text(
        simplejson.dumps(report_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report_path


def print_import_summary(summary: WorkflowSummary, label: str) -> None:
    """Print a normalized import summary line for any retailer workflow.

    Format (identical across all retailers)::

        checkmark <label>: X neu/aktualisiert, Y übersprungen, Z Artikel, N insgesamt in FILE
    """
    print(
        f"ℹ {label}: {summary.processed_count} neu/aktualisiert, "
        f"{summary.skipped_count} übersprungen, {summary.total_items} Artikel, "
        f"{summary.total_receipts} insgesamt in {summary.receipts_file}"
    )

