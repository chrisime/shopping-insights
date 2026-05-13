"""LIDL workflow reporting helpers."""

from __future__ import annotations

import simplejson
from pathlib import Path
from typing import Optional

from config import LidlConfig
from result_types import WorkflowSummary


def write_lidl_skipped_receipts_report(
    skipped_details: list[dict[str, str]],
    report_path: Optional[Path] = None,
) -> Optional[Path]:
    """Write skipped LIDL receipts into a JSON report under tmp/."""
    if not skipped_details:
        return None

    resolved_report_path = report_path or (Path("tmp") / LidlConfig.SKIPPED_RECEIPTS_REPORT_FILE)
    resolved_report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "count": len(skipped_details),
        "skipped_receipts": skipped_details,
    }
    resolved_report_path.write_text(
        simplejson.dumps(report_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return resolved_report_path


def print_lidl_skipped_receipts(
    skipped_details: list[dict[str, str]],
    report_path: Optional[Path],
) -> None:
    """Print skipped LIDL receipts and the optional report location."""
    if not skipped_details:
        return
    print("ℹ Übersprungene LIDL-Bons:")
    for skipped in skipped_details:
        print(f"  - {skipped['receipt_id']}: {skipped['reason']}")
    if report_path:
        print(f"ℹ Skip-Report geschrieben: {report_path}")


def print_lidl_import_summary(summary: WorkflowSummary) -> None:
    """Print a compact Lidl import summary aligned with REWE."""
    print(
        f"✓ LIDL-Kassenbons importiert: {summary.processed_count} neu/aktualisiert, "
        f"{summary.skipped_count} übersprungen, {summary.total_receipts} insgesamt in "
        f"{summary.receipts_file}"
    )


def print_lidl_missing_auth_source() -> None:
    """Print a hint when no LIDL auth source was provided."""
    print("✗ LIDL benötigt --cookies-file oder --browser.")


def print_lidl_workflow_header(title: str) -> None:
    """Print a top-level Lidl workflow section header."""
    print(title)


def print_lidl_existing_receipts_count(existing_receipts_count: int) -> None:
    """Print how many Lidl receipts already exist locally."""
    print(f"Bereits vorhandene Kassenbons: {existing_receipts_count}")


def print_lidl_new_receipts_count(new_receipt_count: int) -> None:
    """Print how many new Lidl receipts will be processed."""
    print(f"Neue Kassenbons zu verarbeiten: {new_receipt_count}")


def print_lidl_checked_pages(checked_pages: int) -> None:
    """Print how many Lidl pages were checked."""
    print(f"Geprüfte Seiten: {checked_pages}")


def print_lidl_processed_pages(total_pages: int) -> None:
    """Print how many Lidl pages were processed in total."""
    print(f"Verarbeitete Seiten: {total_pages}")


def print_lidl_processed_items(total_items: int) -> None:
    """Print how many Lidl items were processed."""
    print(f"Verarbeitete Artikel: {total_items}")


def print_lidl_receipt_collection_start(max_pages: Optional[int] = None) -> None:
    """Print the start message for Lidl receipt-id collection."""
    if max_pages is None:
        print("Sammle alle LIDL-Kassenbon-IDs mit digitalem Kassenbon über API...")
    else:
        print(f"Sammle LIDL-Kassenbon-IDs der ersten {max_pages} Seiten über API...")


def print_lidl_receipt_collection_result(receipt_count: int) -> None:
    """Print the result of Lidl receipt-id collection."""
    print(f"Gefunden: {receipt_count} LIDL-Kassenbon-IDs")

