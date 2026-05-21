"""Interactive menu for REWE workflows."""

from .auth_prompts import prompt_auth_source, prompt_cookies_file
from .common_prompts import (
    print_cancelled,
    print_invalid_choice,
    prompt_optional_value,
    prompt_with_default,
)
from auth.rewe_file_auth import diagnose_rewe_cookie_file
from config import ReweConfig
from workflows.export_workflow import run_export_json_from_db
from workflows.rewe_workflow import run_rewe_initial, run_rewe_update


def _run_rewe_initial() -> None:
    """Interactive wrapper around the central REWE initial workflow."""
    auth_kwargs = prompt_auth_source(
        "REWE",
        "Cookie-/Request-Datei",
        "rewe_cookies.json",
    )
    output_dir = prompt_with_default("Ausgabeverzeichnis für ZIP/PDFs", "tmp/rewe")
    customer_id = prompt_optional_value(
        "Optionale REWE customerId (leer = automatisch ermitteln)"
    )

    print("\nStarte REWE eBon-Import...")
    success = run_rewe_initial(
        customer_id=customer_id,
        output_dir=output_dir,
        **auth_kwargs,
    )
    if success:
        print("✓ REWE-Import erfolgreich abgeschlossen!")
    else:
        print("✗ REWE-Import fehlgeschlagen!")


def _run_rewe_update() -> None:
    """Interactive wrapper around the local REWE update workflow."""
    output_dir = prompt_with_default(
        "Verzeichnis mit vorhandenen REWE ZIP/PDFs",
        "tmp/rewe",
    )

    print("\nStarte REWE Update aus vorhandenen PDFs...")
    success = run_rewe_update(output_dir=output_dir)
    if success:
        print("✓ REWE-Update erfolgreich abgeschlossen!")
    else:
        print("✗ REWE-Update fehlgeschlagen!")


def _run_rewe_export_json() -> None:
    """Export REWE receipts from SQLite into JSON."""

    output_file = prompt_with_default("Zielpfad für JSON-Export", ReweConfig.RECEIPTS_JSON_FILE)
    success = run_export_json_from_db(retailer="rewe", output_file=output_file)
    if not success:
        print("✗ REWE-JSON-Export fehlgeschlagen!")


def _run_rewe_check() -> None:
    """Diagnose a REWE cookie/request file."""
    path = _prompt_rewe_cookies_file()
    success = diagnose_rewe_cookie_file(path)
    if success:
        print("✓ REWE-Cookie-Datei sieht grundsätzlich brauchbar aus!")
    else:
        print("✗ REWE-Cookie-Datei hat Probleme oder ist unvollständig!")


def show_rewe_menu() -> None:
    """Render the REWE submenu and dispatch workflow actions."""
    while True:
        _print_rewe_menu()

        try:
            choice = input("\nWähle eine Option (1-5): ").strip()
            if not _dispatch_rewe_menu_choice(choice):
                return

        except KeyboardInterrupt:
            print_cancelled()
            return


def _print_rewe_menu() -> None:
    """Render the REWE submenu options."""
    print("\n=== REWE: Was möchtest du tun? ===")
    print("1. Initial Setup (ZIP + PDFs + DB-Import)")
    print("2. Update (aus vorhandenen PDFs nur neue eBons importieren)")
    print("3. JSON aus aktuellem DB-Stand erzeugen")
    print("4. Cookie-/Request-Datei prüfen (Diagnose)")
    print("5. Zurück")


def _dispatch_rewe_menu_choice(choice: str) -> bool:
    """Handle a single REWE submenu selection.

    Returns `True` when the menu should keep running and `False` when it should close.
    """
    if choice == "1":
        _run_rewe_initial()
        return False
    if choice == "2":
        _run_rewe_update()
        return False
    if choice == "3":
        _run_rewe_export_json()
        return False
    if choice == "4":
        _run_rewe_check()
        return False
    if choice == "5":
        return False

    print_invalid_choice("1, 2, 3, 4 oder 5")
    return True


def _prompt_rewe_cookies_file() -> str:
    """Prompt for the path to a REWE cookies/request file."""
    return prompt_cookies_file(
        "Pfad zur REWE-Cookie-/Request-Datei",
        "rewe_cookies.json",
    )
