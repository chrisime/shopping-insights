"""Interactive menu for LIDL workflows."""

from auth.lidl_file_auth import diagnose_lidl_cookie_file
from config import LidlConfig
from workflows.lidl_workflow import run_lidl_initial, run_lidl_update

from .auth_prompts import prompt_auth_source, prompt_cookies_file
from .common_prompts import (
    print_cancelled,
    print_invalid_choice,
    prompt_optional_value,
    prompt_with_default,
    run_retailer_export_json,
)

def _prompt_lidl_country() -> str | None:
    """Prompt for an optional LIDL country code override."""
    return prompt_optional_value("Optionaler LIDL-Ländercode (leer = Standardland)")


def _prompt_lidl_output_dir() -> str:
    """Prompt for the local LIDL JSON output directory."""
    return prompt_with_default("Zielverzeichnis für LIDL-JSONs", LidlConfig.DEFAULT_OUTPUT_DIR)


def _run_lidl_initial() -> None:
    """Interactive wrapper around the LIDL initial workflow."""
    auth_kwargs = prompt_auth_source("LIDL", "Cookie-Datei", "lidl_cookies.json")
    country = _prompt_lidl_country()
    output_dir = _prompt_lidl_output_dir()

    print("\nStarte LIDL Kassenbons-Import...")
    success = run_lidl_initial(country=country, output_dir=output_dir, **auth_kwargs)
    if success:
        print("✓ LIDL-Initial erfolgreich abgeschlossen!")
    else:
        print("✗ LIDL-Initial fehlgeschlagen!")


def _run_lidl_update() -> None:
    """Interactive wrapper around the LIDL update workflow."""
    output_dir = _prompt_lidl_output_dir()

    print("\nStarte LIDL Kassenbons-Update...")
    success = run_lidl_update(output_dir=output_dir)
    if success:
        print("✓ LIDL-Update erfolgreich abgeschlossen!")
    else:
        print("✗ LIDL-Update fehlgeschlagen!")


def _run_lidl_export_json() -> None:
    """Export Lidl receipts from SQLite into JSON."""
    run_retailer_export_json("lidl", LidlConfig.RECEIPTS_JSON_FILE)


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
    print("1. Initial (API laden, JSONs speichern, DB befüllen)")
    print("2. Update (lokale JSONs erneut in die DB einspielen)")
    print("3. JSON aus aktuellem DB-Stand erzeugen")
    print("4. Cookie-Datei prüfen (Diagnose)")
    print("5. Zurück")


def _dispatch_lidl_menu_choice(choice: str) -> bool:
    """Handle a single LIDL submenu selection.

    Returns `True` when the menu should keep running and `False` when it should close.
    """
    if choice == "1":
        _run_lidl_initial()
        return False

    if choice == "2":
        _run_lidl_update()
        return False

    if choice == "3":
        _run_lidl_export_json()
        return False

    if choice == "4":
        _run_lidl_check()
        return False

    if choice == "5":
        return False

    print_invalid_choice("1, 2, 3, 4 oder 5")
    return True


def _prompt_lidl_cookies_file() -> str:
    """Prompt for the path to a LIDL cookie file."""
    return prompt_cookies_file(
        "Pfad zur LIDL-Cookie-Datei",
        "lidl_cookies.json",
    )
