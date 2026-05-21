"""Shared interactive auth prompts for retailer CLIs."""

from __future__ import annotations

from typing import Dict

from .common_prompts import print_invalid_choice, prompt_with_default


_BROWSER_CHOICES = {
    "2": "firefox",
    "3": "librewolf",
    "4": "chrome",
    "5": "chromium",
}


def prompt_cookies_file(prompt_text: str, default_path: str) -> str:
    """Prompt for a cookies/request file path with a default value."""
    return prompt_with_default(prompt_text, default_path)


def prompt_auth_source(retailer_label: str, file_option_label: str, default_file_path: str) -> Dict[str, str]:
    """Ask the user whether to use a file or a local browser profile."""
    print(f"\n=== {retailer_label} Authentifizierung ===")
    print(f"1. {file_option_label} (empfohlen)")
    print("2. Lokales Browser-Profil (Firefox)")
    print("3. Lokales Browser-Profil (LibreWolf)")
    print("4. Lokales Browser-Profil (Chrome)")
    print("5. Lokales Browser-Profil (Chromium)")

    while True:
        choice = input("\nWähle eine Option (1-5): ").strip()
        if choice == "1":
            return {
                "cookies_file": prompt_cookies_file(
                    f"Pfad zur {file_option_label}",
                    default_file_path,
                )
            }
        if choice in _BROWSER_CHOICES:
            return {"browser": _BROWSER_CHOICES[choice]}
        print_invalid_choice("1-5")
