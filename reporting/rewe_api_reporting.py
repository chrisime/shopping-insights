"""REWE API/session reporting helpers."""

from __future__ import annotations

from pathlib import Path


def print_rewe_session_test_start() -> None:
    """Print the start message for the REWE session test."""
    print("Teste REWE-Session...")


def print_rewe_session_test_success() -> None:
    """Print the success message for the REWE session test."""
    print("✓ REWE-Session erfolgreich getestet")


def print_rewe_session_test_unexpected_content(content_type: str) -> None:
    """Print a hint when the REWE session test returns unexpected content."""
    print(f"✗ Unerwarteter Inhalt beim Session-Test: {content_type or 'unbekannt'}")


def print_rewe_session_test_request_error(exc: Exception) -> None:
    """Print a REWE session test network error."""
    print(f"✗ Fehler beim Test der REWE-Session: {exc}")


def print_rewe_http_error(status_code: int) -> None:
    """Print a normalized REWE HTTP error message."""
    if status_code == 401:
        print("✗ REWE-Session ungültig oder abgelaufen (401). Bitte Cookies erneuern.")
    elif status_code == 403:
        print("✗ Zugriff verweigert (403). Wahrscheinlich fehlen frische Session-/WAF-Cookies.")
    elif status_code == 404:
        print("✗ REWE-Endpunkt oder customerId ungültig (404).")
    elif status_code == 429:
        print("✗ Rate Limit erreicht (429). Bitte später erneut versuchen.")
    else:
        print(f"✗ HTTP-Fehler beim REWE-Abruf: {status_code}")


def print_rewe_zip_saved(output_path: Path) -> None:
    """Print the success message for a downloaded REWE ZIP archive."""
    print(f"✓ REWE-eBons ZIP gespeichert: {output_path}")


def print_rewe_zip_retry(status_code: int, wait_seconds: int) -> None:
    """Print a retry hint for a failed REWE ZIP HTTP response."""
    print(
        f"⚠ REWE-ZIP-Download fehlgeschlagen ({status_code}), neuer Versuch in {wait_seconds}s..."
    )


def print_rewe_zip_network_retry(wait_seconds: int) -> None:
    """Print a retry hint for a transient REWE ZIP network error."""
    print(
        f"⚠ Netzwerkfehler beim REWE-ZIP-Download, neuer Versuch in {wait_seconds}s..."
    )


def print_rewe_zip_failure(last_exception: object) -> None:
    """Print the final REWE ZIP download failure message."""
    print(f"✗ REWE-ZIP-Download fehlgeschlagen: {last_exception}")


