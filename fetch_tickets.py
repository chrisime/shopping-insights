#!/usr/bin/env python3
"""
Receipt Data Updater - Entry Point

Main entry point for the shopping analyzer application. Supports multiple
retailers (currently LIDL and REWE).

For first-time setup or complete refresh, use the 'initial' command.
For monthly updates (adds only new data), use the 'update' command.
Use the 'check' command to validate cookie/request files before running imports.
Use the 'export' command to generate JSON from the current SQLite database state.

Usage:
    python fetch_tickets.py                                              # Interactive menu
    python fetch_tickets.py initial --retailer lidl --browser firefox    # LIDL initial setup
    python fetch_tickets.py update  --retailer lidl                      # LIDL update from local JSONs
    python fetch_tickets.py initial --retailer lidl --cookies-file cookies.json
    python fetch_tickets.py initial --retailer lidl --output-dir tmp/lidl
    python fetch_tickets.py initial --retailer rewe --cookies-file rewe_cookies.json
    python fetch_tickets.py update  --retailer rewe --output-dir tmp/rewe
    python fetch_tickets.py check   --retailer lidl --cookies-file lidl_cookies.json
    python fetch_tickets.py check   --retailer rewe --cookies-file rewe_cookies.json
    python fetch_tickets.py export  --retailer lidl --output-file lidl_receipts.json
"""

from __future__ import annotations

import argparse
import sys

from config import LidlConfig, ReweConfig
from shared.retailer_runtime import RETAILERS


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="fetch_tickets.py",
        description="Extract and manage receipt data from supported retailers (LIDL, REWE).",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    def add_retailer_arg(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "--retailer",
            choices=RETAILERS,
            default="lidl",
            help="Retailer to fetch data for (default: lidl)",
        )

    # Common arguments shared by workflow commands
    def add_workflow_args(subparser: argparse.ArgumentParser) -> None:
        add_retailer_arg(subparser)
        group = subparser.add_mutually_exclusive_group()
        group.add_argument(
            "--browser",
            choices=["firefox", "librewolf", "chrome", "chromium"],
            help="Browser to extract cookies from (non-interactive mode). "
                 "LIDL/REWE: firefox/librewolf/chrome/chromium.",
        )
        group.add_argument(
            "--cookies-file",
            metavar="FILE",
            help="Path to cookies/request JSON file (non-interactive mode)",
        )
        # LIDL-specific
        subparser.add_argument(
            "--country",
            metavar="CODE",
            help="[LIDL only] Two-letter country code (e.g., 'de', 'bg', 'nl'). Default: de",
        )
        # REWE-specific
        subparser.add_argument(
            "--customer-id",
            metavar="UUID",
            help="[REWE only] REWE customerId used by the ZIP endpoint "
                 "(optional if detectable from session/file/cache)",
        )
        subparser.add_argument(
            "--output-dir",
            metavar="DIR",
            help="Directory where downloaded receipts are stored (default: tmp/<retailer>)",
        )
    def add_check_args(subparser: argparse.ArgumentParser) -> None:
        add_retailer_arg(subparser)
        subparser.add_argument(
            "--cookies-file",
            metavar="FILE",
            help="Path to cookies/request JSON file to validate",
        )

    def add_export_args(subparser: argparse.ArgumentParser) -> None:
        add_retailer_arg(subparser)
        subparser.add_argument(
            "--output-file",
            metavar="FILE",
            help="Optional output path for exported JSON (defaults to retailer json target)",
        )


    initial_parser = subparsers.add_parser(
        "initial",
        help="Extract all historical receipt data (first-time setup)",
    )
    add_workflow_args(initial_parser)

    update_parser = subparsers.add_parser(
        "update",
        help="Add only new receipts since last run",
    )
    add_workflow_args(update_parser)

    check_parser = subparsers.add_parser(
        "check",
        help="Validate a retailer-specific cookie/request file before import",
    )
    add_check_args(check_parser)

    export_parser = subparsers.add_parser(
        "export",
        help="Export receipts from SQLite into JSON",
    )
    add_export_args(export_parser)

    return parser


def _dispatch(args: argparse.Namespace, mode: str) -> bool:
    if mode == "check":
        return _dispatch_check(args)
    if mode == "export":
        return _dispatch_export(args)
    return _dispatch_workflow(args, mode)


def _dispatch_check(args: argparse.Namespace) -> bool:
    """Run retailer-specific cookie/request diagnostics."""
    if args.retailer == "lidl":
        from auth.lidl_file_auth import diagnose_lidl_cookie_file

        return diagnose_lidl_cookie_file(args.cookies_file)

    if args.retailer == "rewe":
        from auth.rewe_file_auth import diagnose_rewe_cookie_file

        return diagnose_rewe_cookie_file(args.cookies_file)

    print(f"✗ Unbekannter Händler: {args.retailer}", file=sys.stderr)
    return False


def _dispatch_workflow(args: argparse.Namespace, mode: str) -> bool:
    """Run the requested retailer workflow for `initial` or `update`."""
    from workflows.lidl_workflow import run_lidl_initial, run_lidl_update
    from workflows.rewe_workflow import run_rewe_initial, run_rewe_update

    if args.retailer == "lidl":
        output_dir = args.output_dir or LidlConfig.DEFAULT_OUTPUT_DIR
        if mode == "initial":
            return run_lidl_initial(
                browser=args.browser,
                cookies_file=args.cookies_file,
                country=args.country,
                output_dir=output_dir,
            )
        return run_lidl_update(output_dir=output_dir)

    if args.retailer == "rewe":
        output_dir = args.output_dir or ReweConfig.REWE_DEFAULT_OUTPUT_DIR
        if mode == "initial":
            return run_rewe_initial(
                browser=args.browser,
                cookies_file=args.cookies_file,
                customer_id=args.customer_id,
                output_dir=output_dir,
            )
        return run_rewe_update(output_dir=output_dir)

    print(f"✗ Unbekannter Händler: {args.retailer}", file=sys.stderr)
    return False


def _dispatch_export(args: argparse.Namespace) -> bool:
    """Run JSON export from current SQLite state for one retailer."""
    from workflows.export_workflow import run_export_json_from_db

    return run_export_json_from_db(
        retailer=args.retailer,
        output_file=args.output_file,
    )


def _command_label(command: str) -> str:
    """Return the user-facing label for a subcommand."""
    if command == "initial":
        return "Initial Setup"
    if command == "update":
        return "Update"
    if command == "export":
        return "Export"
    return "Check"


def _run_subcommand(args: argparse.Namespace) -> int:
    """Execute a parsed subcommand and return the process exit code."""
    try:
        success = _dispatch(args, args.command)
    except ModuleNotFoundError as exc:
        _print_missing_dependency_hint(exc)
        return 1
    label = _command_label(args.command)
    if success:
        print(f"✓ {label} erfolgreich abgeschlossen!")
        return 0

    print(f"✗ {label} fehlgeschlagen!")
    return 1


def _run_interactive_menu() -> int:
    """Start the interactive CLI menu and return a process exit code."""
    try:
        from cli import main as run_cli_main
    except ModuleNotFoundError as exc:
        _print_missing_dependency_hint(exc)
        return 1

    try:
        run_cli_main()
    except ModuleNotFoundError as exc:
        _print_missing_dependency_hint(exc)
        return 1
    return 0


def _print_missing_dependency_hint(exc: ModuleNotFoundError) -> None:
    """Print a concise installation hint when a required package is missing."""
    missing_module = str(getattr(exc, "name", "") or "unbekannt")
    print(
        (
            "✗ Fehlende Python-Abhängigkeit: "
            f"{missing_module}.\n"
            "Bitte installiere die Projektabhängigkeiten und starte den Befehl erneut:\n"
            "  python3.14 -m pip install -r requirements.txt"
        ),
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    """Public application entry point for CLI and tests."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command in ("initial", "update", "check", "export"):
        return _run_subcommand(args)

    return _run_interactive_menu()


if __name__ == "__main__":
    sys.exit(main())
