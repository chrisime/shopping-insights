"""Interactive menu for Rossmann workflows."""

from .auth_prompts import prompt_cookies_file
from .common_prompts import (
    print_cancelled,
    print_invalid_choice,
    prompt_optional_value,
    prompt_with_default,
    run_retailer_export_json,
)
from config import RossmannConfig
from workflows.rossmann_workflow import run_rossmann_initial, run_rossmann_update


def _run_rossmann_initial() -> None:
    """Interactive wrapper around the central Rossmann initial workflow."""
    output_dir = prompt_with_default(
        "Ausgabeverzeichnis für Belege",
        "tmp/rossmann",
    )
    account_id = prompt_optional_value("Optionale Rossmann accountId (leer = Login)")
    account_hash = prompt_optional_value("Optionale Rossmann accountHash (leer = Login)")
    prompt_login = False
    if not (account_id and account_hash):
        login_answer = input(
            "Rossmann accountId/accountHash fehlen oder sind unvollständig. "
            "Stattdessen interaktiv mit E-Mail/Passwort einloggen? (j/N): "
        ).strip().lower()
        prompt_login = login_answer in ("j", "ja", "y", "yes", "1")

    print("\nStarte Rossmann Beleg-Import...")
    success = run_rossmann_initial(
        output_dir=output_dir,
        account_id=account_id,
        account_hash=account_hash,
        prompt_login=prompt_login,
    )
    if success:
        print("✓ Rossmann-Import erfolgreich abgeschlossen!")
    else:
        print("✗ Rossmann-Import fehlgeschlagen!")


def _run_rossmann_update() -> None:
    """Interactive wrapper around the local Rossmann update workflow."""
    output_dir = prompt_with_default(
        "Verzeichnis mit vorhandenen Rossmann Beleg-JSONs",
        "tmp/rossmann",
    )

    print("\nStarte Rossmann Update aus vorhandenen Beleg-JSONs...")
    success = run_rossmann_update(output_dir=output_dir)
    if success:
        print("✓ Rossmann-Update erfolgreich abgeschlossen!")
    else:
        print("✗ Rossmann-Update fehlgeschlagen!")


def _run_rossmann_export_json() -> None:
    """Export Rossmann receipts from SQLite into JSON."""
    run_retailer_export_json("rossmann", RossmannConfig.RECEIPTS_JSON_FILE)


def show_rossmann_menu() -> None:
    """Render the Rossmann submenu and dispatch workflow actions."""
    while True:
        _print_rossmann_menu()

        try:
            choice = input("\nWähle eine Option (1-4): ").strip()
            if not _dispatch_rossmann_menu_choice(choice):
                return

        except KeyboardInterrupt:
            print_cancelled()
            return


def _print_rossmann_menu() -> None:
    """Render the Rossmann submenu options."""
    print("\n=== Rossmann: Was möchtest du tun? ===")
    print("1. Initial Setup (Belege + PDFs + DB-Import)")
    print("2. Update (aus vorhandenen Beleg-JSONs nur neue importieren)")
    print("3. JSON aus aktuellem DB-Stand erzeugen")
    print("4. Zurück")


def _dispatch_rossmann_menu_choice(choice: str) -> bool:
    """Handle a single Rossmann submenu selection.

    Returns `True` when the menu should keep running and `False` when it should close.
    """
    if choice == "1":
        _run_rossmann_initial()
        return False
    if choice == "2":
        _run_rossmann_update()
        return False
    if choice == "3":
        _run_rossmann_export_json()
        return False
    if choice == "4":
        return False

    print_invalid_choice("1, 2, 3 oder 4")
    return True
