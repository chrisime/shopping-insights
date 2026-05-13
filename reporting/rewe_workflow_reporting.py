"""REWE workflow reporting helpers."""

from __future__ import annotations

import simplejson
from pathlib import Path
from typing import Optional

from config import ReweConfig
from result_types import WorkflowSummary


def write_rewe_skipped_receipts_report(
    pdf_dir: Path,
    skipped_details: list[dict],
) -> Optional[Path]:
    """Write skipped REWE receipts into a JSON report next to the ZIP/PDF output."""
    if not skipped_details:
        return None

    report_path = pdf_dir.parent / ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE
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


def print_rewe_skipped_receipts(
    skipped_details: list[dict],
    report_path: Optional[Path],
) -> None:
    """Print skipped REWE receipts and the optional report location."""
    if not skipped_details:
        return
    print("ℹ Übersprungene REWE-Bons:")
    for skipped in skipped_details:
        print(f"  - {skipped['file']}: {skipped['reason']}")
    if report_path:
        print(f"ℹ Skip-Report geschrieben: {report_path}")


def print_rewe_import_summary(summary: WorkflowSummary) -> None:
    """Print a compact REWE import summary."""
    print(
        f"✓ REWE-eBons importiert: {summary.processed_count} neu/aktualisiert, "
        f"{summary.skipped_count} übersprungen, {summary.total_items} Artikel, "
        f"{summary.total_receipts} insgesamt in "
        f"{summary.receipts_file}"
    )


def print_rewe_update_no_delta() -> None:
    """Explain that REWE updates now refill the target store from local PDFs via upsert."""
    print("ℹ REWE: importiere alle vorhandenen PDFs lokal per Upsert neu.")


def print_rewe_missing_auth_source() -> None:
    """Print a hint when no REWE auth source was provided."""
    print("✗ REWE benötigt --cookies-file oder --browser.")


def print_rewe_no_pdfs_found(pdf_dir: Path) -> None:
    """Print that no REWE PDFs were found for import."""
    print(f"⚠ Keine REWE-PDFs zum Importieren gefunden in: {pdf_dir}")


def print_rewe_zip_extracted(output_dir: Path) -> None:
    """Print the success message after extracting a REWE ZIP archive."""
    print(f"✓ REWE-eBons entpackt nach: {output_dir}")


