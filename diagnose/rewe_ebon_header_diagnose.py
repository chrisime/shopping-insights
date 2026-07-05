"""Diagnose helper for REWE eBon header/store/address extraction.

Usage:
    python diagnose/rewe_ebon_header_diagnose.py "/path/to/Dein REWE eBon vom 09.05.2025.pdf"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pdfplumber
import simplejson

# Allow running this script directly via `python diagnose/...py`.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from parsing.rewe_info_extractor import extract_rewe_receipt_info


FOOTER_START_RE = re.compile(r"^(?:UID\s*Nr\.?|UID-Nr\.?|USt-IdNr\.?|USt\.?-IdNr\.?)", re.IGNORECASE)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Diagnose REWE eBon header extraction (store/address/metadata).",
    )
    parser.add_argument("pdf", type=Path, help="Path to a REWE eBon PDF")
    parser.add_argument(
        "--max-lines",
        type=int,
        default=20,
        help="How many lines to print from full text/header/footer (default: 20)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full diagnosis as JSON instead of human-readable text",
    )
    return parser


def _extract_header_lines(lines: list[str]) -> list[str]:
    header: list[str] = []
    for line in lines:
        if line == "EUR" or FOOTER_START_RE.match(line.strip()):
            break
        header.append(line)
    return header


def _extract_footer_lines(lines: list[str]) -> list[str]:
    for index, line in enumerate(lines):
        if FOOTER_START_RE.match(line.strip()):
            return lines[index + 1 :]
    return []


def _print_lines(title: str, lines: list[str], max_lines: int) -> None:
    print(f"\n=== {title} ({len(lines)}) ===")
    for idx, line in enumerate(lines[:max_lines], 1):
        print(f"{idx:>3}: {line}")
    if len(lines) > max_lines:
        print(f"... ({len(lines) - max_lines} more lines)")


def run(pdf_path: Path, max_lines: int, as_json: bool) -> int:
    if not pdf_path.exists():
        print(f"ERROR: file not found: {pdf_path}")
        return 2

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages)
        page_count = len(pdf.pages)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        print("ERROR: no readable text in PDF")
        return 3

    header_lines = _extract_header_lines(lines)
    footer_lines = _extract_footer_lines(lines)
    metadata = extract_rewe_receipt_info(text, lines)

    diagnosis = {
        "file": str(pdf_path),
        "pages": page_count,
        "line_count": len(lines),
        "header_lines": header_lines,
        "footer_lines": footer_lines,
        "extracted": {
            "store": metadata.get("store"),
            "address": metadata.get("address"),
            "market": metadata.get("market"),
            "register": metadata.get("register"),
            "cashier": metadata.get("cashier"),
            "purchase_date": metadata.get("purchase_date"),
            "id": metadata.get("id"),
            "total_price": metadata.get("total_price"),
        },
    }

    if as_json:
        print(simplejson.dumps(diagnosis, ensure_ascii=False, indent=2))
        return 0

    print("=== REWE eBon Diagnose ===")
    print(f"File: {pdf_path}")
    print(f"Pages: {page_count}")
    print(f"Text lines: {len(lines)}")

    _print_lines("HEADER", header_lines, max_lines)
    _print_lines("FOOTER", footer_lines, max_lines)

    print("\n=== EXTRACTED ===")
    print(f"store        : {metadata.get('store')}")
    print(f"address      : {metadata.get('address')}")
    print(f"market       : {metadata.get('market')}")
    print(f"register     : {metadata.get('register')}")
    print(f"cashier      : {metadata.get('cashier')}")
    print(f"purchase_date: {metadata.get('purchase_date')}")
    print(f"id           : {metadata.get('id')}")
    print(f"total_price  : {metadata.get('total_price')}")

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run(args.pdf, args.max_lines, args.json)


if __name__ == "__main__":
    raise SystemExit(main())



