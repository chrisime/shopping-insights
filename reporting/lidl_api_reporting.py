"""LIDL API/session reporting helpers."""

from __future__ import annotations


def print_lidl_session_test_start() -> None:
    """Print the start message for the LIDL session test."""
    print("Teste LIDL-Session...")


def print_lidl_session_test_success(receipt_count: int | None = None) -> None:
    """Print the success message for the LIDL session test."""
    if receipt_count is None:
        print("✓ LIDL-Session erfolgreich getestet")
    else:
        print(f"✓ LIDL-Session erfolgreich getestet ({receipt_count} Kassenbons gefunden)")


def print_lidl_session_test_no_receipts() -> None:
    """Print that the LIDL session is valid but no receipts were returned."""
    print("✓ LIDL-Session erfolgreich getestet (keine Kassenbons in der API-Antwort)")


def print_lidl_session_test_unauthorized() -> None:
    """Print a normalized unauthorized message for the LIDL session test."""
    print("✗ LIDL-Session ungültig oder abgelaufen (401). Bitte Cookies erneuern.")


def print_lidl_session_test_http_error(status_code: int, exc: Exception) -> None:
    """Print a normalized LIDL HTTP error for the session test."""
    print(f"✗ API-Verbindungsfehler ({status_code}): {exc}")


def print_lidl_session_test_request_error(exc: Exception) -> None:
    """Print a LIDL request/network error for the session test."""
    print(f"✗ API-Verbindungsfehler: {exc}")


def print_lidl_session_test_json_error(exc: Exception) -> None:
    """Print a JSON decode error for the LIDL session test."""
    print(f"✗ JSON-Decodierungsfehler: {exc}")

