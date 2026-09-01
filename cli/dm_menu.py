"""Interactive menu for dm workflows."""

from .auth_prompts import prompt_auth_source, prompt_cookies_file
from .common_prompts import (
    print_cancelled,
    print_invalid_choice,
    prompt_with_default,
    run_retailer_export_json,
)
from auth.dm_file_auth import diagnose_dm_cookie_file
from config import DmConfig
from workflows.dm_workflow import run_dm_initial, run_dm_update


def _run_dm_initial() -> None:
    """Interactive wrapper around the central dm initial workflow."""
    auth_kwargs = prompt_auth_source(
        "dm",
        "Cookie-Datei",
        "dm_cookies.json",
    )
    output_dir = prompt_with_default(
        "Ausgabeverzeichnis für eBons",
        "tmp/dm",
    )

    print("\nStarte dm eBon-Import...")
    success = run_dm_initial(
        output_dir=output_dir,
        browser=auth_kwargs.get("browser"),
        cookies_file=auth_kwargs.get("cookies_file"),
    )
    if success:
        print("✓ dm-Import erfolgreich abgeschlossen!")
    else:
        print("✗ dm-Import fehlgeschlagen!")


def _run_dm_update() -> None:
    """Interactive wrapper around the local dm update workflow."""
    output_dir = prompt_with_default(
        "Verzeichnis mit vorhandenen dm eBon-JSONs",
        "tmp/dm",
    )

    print("\nStarte dm Update aus vorhandenen eBon-JSONs...")
    success = run_dm_update(output_dir=output_dir)
    if success:
        print("✓ dm-Update erfolgreich abgeschlossen!")
    else:
        print("✗ dm-Update fehlgeschlagen!")


def _run_dm_export_json() -> None:
    """Export dm receipts from SQLite into JSON."""
    run_retailer_export_json("dm", DmConfig.RECEIPTS_JSON_FILE)


def _run_dm_check() -> None:
    """Diagnose a dm cookie/request file."""
    path = _prompt_dm_cookies_file()
    success = diagnose_dm_cookie_file(path)
    if success:
        print("✓ dm-Cookie-Datei sieht grundsätzlich brauchbar aus!")
    else:
        print("✗ dm-Cookie-Datei hat Probleme oder ist unvollständig!")


def show_dm_menu() -> None:
    """Render the dm submenu and dispatch workflow actions."""
    while True:
        _print_dm_menu()

        try:
            choice = input("\nWähle eine Option (1-5): ").strip()
            if not _dispatch_dm_menu_choice(choice):
                return

        except KeyboardInterrupt:
            print_cancelled()
            return


def _print_dm_menu() -> None:
    """Render the dm submenu options."""
    print("\n=== dm: Was möchtest du tun? ===")
    print("1. Initial Setup (Kaufhistorie + eBons + DB-Import)")
    print("2. Update (aus vorhandenen eBon-JSONs nur neue importieren)")
    print("3. JSON aus aktuellem DB-Stand erzeugen")
    print("4. Cookie-Datei prüfen (Diagnose)")
    print("5. Zurück")


def _dispatch_dm_menu_choice(choice: str) -> bool:
    """Handle a single dm submenu selection.

    Returns `True` when the menu should keep running and `False` when it should close.
    """
    if choice == "1":
        _run_dm_initial()
        return False
    if choice == "2":
        _run_dm_update()
        return False
    if choice == "3":
        _run_dm_export_json()
        return False
    if choice == "4":
        _run_dm_check()
        return False
    if choice == "5":
        return False

    print_invalid_choice("1, 2, 3, 4 oder 5")
    return True


def _prompt_dm_cookies_file() -> str:
    """Prompt for the path to a dm cookies/request file."""
    return prompt_cookies_file(
        "Pfad zur dm-Cookie-Datei",
        "dm_cookies.json",
    )
