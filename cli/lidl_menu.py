"""Interactive menu for LIDL workflows."""

from auth.lidl_file_auth import diagnose_lidl_cookie_file
from config import LidlConfig
from workflows.export_workflow import run_export_json_from_db
from workflows.lidl_workflow import run_lidl_sync

from .auth_prompts import prompt_auth_source, prompt_cookies_file
from .common_prompts import (
    print_cancelled,
    print_invalid_choice,
    prompt_optional_value,
    prompt_with_default,
)

def _prompt_lidl_country() -> str | None:
    """Prompt for an optional LIDL country code override."""
    return prompt_optional_value("Optionaler LIDL-Ländercode (leer = Standardland)")


def _run_lidl_sync() -> None:
    """Interactive wrapper around the central LIDL sync workflow."""
    auth_kwargs = prompt_auth_source("LIDL", "Cookie-Datei", "lidl_cookies.json")
    country = _prompt_lidl_country()

    print("\nStarte LIDL-Sync...")
    success = run_lidl_sync(country=country, **auth_kwargs)
    if success:
        print("✓ LIDL-Sync erfolgreich abgeschlossen!")
    else:
        print("✗ LIDL-Sync fehlgeschlagen!")


def _run_lidl_export_json() -> None:
    """Export Lidl receipts from SQLite into JSON."""

    output_file = prompt_with_default("Zielpfad für JSON-Export", LidlConfig.RECEIPTS_JSON_FILE)
    success = run_export_json_from_db(retailer="lidl", output_file=output_file)
    if not success:
        print("✗ LIDL-JSON-Export fehlgeschlagen!")


def _run_lidl_check() -> None:
    """Diagnose a LIDL cookie file."""
    path = _prompt_lidl_cookies_file()
    success = diagnose_lidl_cookie_file(path)
    if success:
        print("✓ LIDL-Cookie-Datei sieht grundsätzlich brauchbar aus!")
    else:
        print("✗ LIDL-Cookie-Datei hat Probleme oder ist unvollständig!")


def show_lidl_menu() -> None:
    """Render the LIDL submenu and dispatch workflow actions."""
    while True:
        _print_lidl_menu()
        try:
            choice = input("\nWähle eine Option (1-4): ").strip()
            if not _dispatch_lidl_menu_choice(choice):
                return

        except KeyboardInterrupt:
            print_cancelled()
            return


def _print_lidl_menu() -> None:
    """Render the LIDL submenu options."""
    print("\n=== LIDL: Welche Aktion möchtest du ausführen? ===")
    print("1. Sync (Alle Seiten prüfen, neue/geänderte Kassenbons importieren)")
    print("2. JSON aus aktuellem DB-Stand erzeugen")
    print("3. Cookie-Datei prüfen (Diagnose)")
    print("4. Zurück")


def _dispatch_lidl_menu_choice(choice: str) -> bool:
    """Handle a single LIDL submenu selection.

    Returns `True` when the menu should keep running and `False` when it should close.
    """
    if choice == "1":
        _run_lidl_sync()
        return False

    if choice == "2":
        _run_lidl_export_json()
        return False

    if choice == "3":
        _run_lidl_check()
        return False

    if choice == "4":
        return False

    print_invalid_choice("1, 2, 3 oder 4")
    return True


def _prompt_lidl_cookies_file() -> str:
    """Prompt for the path to a LIDL cookie file."""
    return prompt_cookies_file(
        "Pfad zur LIDL-Cookie-Datei",
        "lidl_cookies.json",
    )
