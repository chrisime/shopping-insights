"""
Receipt Data Updater - Entry Point

Main entry point for the shopping analyzer application. Supports multiple
retailers (currently LIDL and REWE).

For first-time setup or complete refresh, use the 'initial' command.
For monthly updates (adds only new data and sorts by date), use the 'update' command.
Use the 'check' command to validate cookie/request files before running imports.

Usage:
    python get_data.py                                              # Interactive menu
    python get_data.py initial --retailer lidl --browser firefox    # LIDL initial setup
    python get_data.py update  --retailer lidl --browser chromium   # LIDL update
    python get_data.py initial --retailer lidl --cookies-file cookies.json
    python get_data.py update  --retailer lidl --country bg --browser chromium
    python get_data.py initial --retailer lidl --write-backend json

    python get_data.py initial --retailer rewe --cookies-file rewe_cookies.json
    python get_data.py update  --retailer rewe --output-dir tmp/rewe
    python get_data.py check   --retailer lidl --cookies-file lidl_cookies.json
    python get_data.py check   --retailer rewe --cookies-file rewe_cookies.json
"""

import argparse
import sys

from storage import WRITE_BACKENDS


RETAILERS = ("lidl", "rewe")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="get_data.py",
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
            default="tmp/rewe",
            help="[REWE only] Directory where the ZIP and extracted PDFs are stored",
        )
        subparser.add_argument(
            "--write-backend",
            choices=WRITE_BACKENDS,
            default="json",
            help="Write backend used for receipt persistence (default: json)",
        )

    def add_check_args(subparser: argparse.ArgumentParser) -> None:
        add_retailer_arg(subparser)
        subparser.add_argument(
            "--cookies-file",
            metavar="FILE",
            help="Path to cookies/request JSON file to validate",
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

    return parser


def _dispatch(args: argparse.Namespace, mode: str) -> bool:
    if mode == "check":
        return _dispatch_check(args)
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
    from workflows.lidl_workflow import run_lidl_sync
    from workflows.rewe_workflow import run_rewe_initial, run_rewe_update

    if args.retailer == "lidl":
        return run_lidl_sync(
            browser=args.browser,
            cookies_file=args.cookies_file,
            country=args.country,
            write_backend=args.write_backend,
        )

    if args.retailer == "rewe":
        workflow_func = run_rewe_initial if mode == "initial" else run_rewe_update
        return workflow_func(
            browser=args.browser,
            cookies_file=args.cookies_file,
            customer_id=args.customer_id,
            output_dir=args.output_dir,
            write_backend=args.write_backend,
        )

    print(f"✗ Unbekannter Händler: {args.retailer}", file=sys.stderr)
    return False


def _command_label(command: str) -> str:
    """Return the user-facing label for a subcommand."""
    if command == "initial":
        return "Initial Setup"
    if command == "update":
        return "Update"
    return "Check"


def _run_subcommand(args: argparse.Namespace) -> int:
    """Execute a parsed subcommand and return the process exit code."""
    success = _dispatch(args, args.command)
    label = _command_label(args.command)
    if success:
        print(f"✓ {label} erfolgreich abgeschlossen!")
        return 0

    print(f"✗ {label} fehlgeschlagen!")
    return 1


def _run_interactive_menu() -> int:
    """Start the interactive CLI menu and return a process exit code."""
    from cli import main as run_cli_main

    run_cli_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Public application entry point for CLI and tests."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command in ("initial", "update", "check"):
        return _run_subcommand(args)

    return _run_interactive_menu()


if __name__ == "__main__":
    sys.exit(main())
