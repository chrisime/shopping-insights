"""Main menu interface for the shopping analyzer."""

from .lidl_menu import show_lidl_menu
from .rewe_menu import show_rewe_menu


def main() -> None:
    """Main menu: choose retailer first, then the operation."""
    while True:
        _print_main_menu()

        try:
            choice = input("\nWähle eine Option (1-3): ").strip()
            if _dispatch_main_menu_choice(choice):
                continue
            return

        except KeyboardInterrupt:
            print("\n\nProgramm unterbrochen.")
            return
        except Exception as e:
            print(f"Ein Fehler ist aufgetreten: {e}")
            return


def _print_main_menu() -> None:
    """Render the retailer selection menu."""
    print("\n=== Willkommen! Für welchen Händler möchtest du Kassenbons verwalten? ===")
    print("1. LIDL")
    print("2. REWE")
    print("3. Beenden")


def _dispatch_main_menu_choice(choice: str) -> bool:
    """Handle a single main-menu selection.

    Returns `True` when the menu loop should continue and `False` when it should end.
    """
    if choice == "1":
        show_lidl_menu()
        return True
    if choice == "2":
        show_rewe_menu()
        return True
    if choice == "3":
        print("Auf Wiedersehen!")
        return False

    print("Ungültige Eingabe. Bitte wähle 1, 2 oder 3.")
    return True
