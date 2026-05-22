"""Common prompt and message helpers for interactive CLI menus."""

from __future__ import annotations


def prompt_with_default(prompt_text: str, default_value: str) -> str:
    """Prompt for a string value and fall back to a default on empty input."""
    value = input(f"{prompt_text} [{default_value}]: ").strip()
    return value or default_value


def prompt_optional_value(prompt_text: str) -> str | None:
    """Prompt for an optional string value and return None on empty input."""
    value = input(f"{prompt_text}: ").strip()
    return value or None



def print_invalid_choice(valid_options_text: str) -> None:
    """Print a normalized invalid-choice message for interactive menus."""
    print(f"Ungültige Eingabe. Bitte wähle {valid_options_text}.")


def print_cancelled() -> None:
    """Print a normalized cancellation message for interactive menus."""
    print("\n\nAbgebrochen.")


def run_retailer_export_json(retailer: str, default_receipts_json_file: str) -> None:
    """Prompt for export path and run JSON export for one retailer."""
    from workflows.export_workflow import run_export_json_from_db

    output_file = prompt_with_default("Zielpfad für JSON-Export", default_receipts_json_file)
    success = run_export_json_from_db(retailer=retailer, output_file=output_file)
    if not success:
        print(f"✗ {retailer.upper()}-JSON-Export fehlgeschlagen!")

