"""Common prompt and message helpers for interactive CLI menus."""

from __future__ import annotations

from storage import WRITE_BACKENDS


def prompt_with_default(prompt_text: str, default_value: str) -> str:
    """Prompt for a string value and fall back to a default on empty input."""
    value = input(f"{prompt_text} [{default_value}]: ").strip()
    return value or default_value


def prompt_optional_value(prompt_text: str) -> str | None:
    """Prompt for an optional string value and return None on empty input."""
    value = input(f"{prompt_text}: ").strip()
    return value or None


def prompt_write_backend(default_backend: str = "json") -> str:
    """Prompt for the configured receipt write backend."""
    options = list(WRITE_BACKENDS)
    if default_backend not in options:
        default_backend = options[0]
    default_index = options.index(default_backend) + 1

    print("Speicherziel für Bons:")
    for index, backend in enumerate(options, start=1):
        print(f"{index}. {backend}")

    while True:
        choice = input(f"Wähle ein Speicherziel [Standard: {default_index}]: ").strip()
        if not choice:
            return default_backend
        if choice.isdigit():
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(options):
                return options[selected_index]
        if choice.lower() in options:
            return choice.lower()
        print_invalid_choice(", ".join(str(index) for index in range(1, len(options) + 1)))


def print_invalid_choice(valid_options_text: str) -> None:
    """Print a normalized invalid-choice message for interactive menus."""
    print(f"Ungültige Eingabe. Bitte wähle {valid_options_text}.")


def print_cancelled() -> None:
    """Print a normalized cancellation message for interactive menus."""
    print("\n\nAbgebrochen.")

