import argparse
import io
import unittest
from unittest.mock import patch

import fetch_tickets


class GetDataTests(unittest.TestCase):
    def test_create_parser_parses_check_command(self):
        parser = fetch_tickets.create_parser()

        args = parser.parse_args(
            ["check", "--retailer", "lidl", "--cookies-file", "lidl_cookies.json"]
        )

        self.assertEqual(args.command, "check")
        self.assertEqual(args.retailer, "lidl")
        self.assertEqual(args.cookies_file, "lidl_cookies.json")

    def test_create_parser_parses_export_command(self):
        parser = fetch_tickets.create_parser()

        args = parser.parse_args([
            "export",
            "--retailer",
            "lidl",
            "--output-file",
            "lidl_receipts.json",
        ])

        self.assertEqual(args.command, "export")
        self.assertEqual(args.output_file, "lidl_receipts.json")

    def test_dispatch_check_calls_lidl_diagnostics(self):
        args = argparse.Namespace(
            retailer="lidl",
            cookies_file="lidl_cookies.json",
        )

        with patch("auth.lidl_file_auth.diagnose_lidl_cookie_file", return_value=True) as diagnose:
            success = fetch_tickets._dispatch(args, "check")

        self.assertTrue(success)
        diagnose.assert_called_once_with("lidl_cookies.json")

    def test_dispatch_check_calls_rewe_diagnostics(self):
        args = argparse.Namespace(
            retailer="rewe",
            cookies_file="rewe_cookies.json",
        )

        with patch("auth.rewe_file_auth.diagnose_rewe_cookie_file", return_value=True) as diagnose:
            success = fetch_tickets._dispatch(args, "check")

        self.assertTrue(success)
        diagnose.assert_called_once_with("rewe_cookies.json")

    def test_dispatch_update_calls_rewe_workflow_without_auth_requirements(self):
        args = argparse.Namespace(
            retailer="rewe",
            browser=None,
            cookies_file=None,
            customer_id=None,
            output_dir="tmp/rewe",
            country=None,
        )

        with patch("workflows.rewe_workflow.run_rewe_update", return_value=True) as run_update:
            success = fetch_tickets._dispatch(args, "update")

        self.assertTrue(success)
        run_update.assert_called_once_with(output_dir="tmp/rewe")

    def test_dispatch_initial_calls_lidl_sync(self):
        args = argparse.Namespace(
            retailer="lidl",
            browser="firefox",
            cookies_file=None,
            customer_id=None,
            output_dir="tmp/rewe",
            country="de",
        )

        with patch("workflows.lidl_workflow.run_lidl_initial", return_value=True) as run_sync:
            success = fetch_tickets._dispatch(args, "initial")

        self.assertTrue(success)
        run_sync.assert_called_once_with(
            browser="firefox",
            cookies_file=None,
            country="de",
            output_dir="tmp/rewe",
        )

    def test_dispatch_update_calls_lidl_sync(self):
        args = argparse.Namespace(
            retailer="lidl",
            browser=None,
            cookies_file="lidl_cookies.json",
            customer_id=None,
            output_dir="tmp/rewe",
            country="de",
        )

        with patch("workflows.lidl_workflow.run_lidl_update", return_value=True) as run_sync:
            success = fetch_tickets._dispatch(args, "update")

        self.assertTrue(success)
        run_sync.assert_called_once_with(output_dir="tmp/rewe")

    def test_dispatch_export_calls_export_workflow(self):
        args = argparse.Namespace(
            retailer="rewe",
            output_file="rewe_receipts.json",
        )

        with patch("workflows.export_workflow.run_export_json_from_db", return_value=True) as run_export:
            success = fetch_tickets._dispatch(args, "export")

        self.assertTrue(success)
        run_export.assert_called_once_with(
            retailer="rewe",
            output_file="rewe_receipts.json",
        )

    def test_main_runs_interactive_cli_when_no_subcommand_is_given(self):
        with patch("cli.main") as cli_main:
            exit_code = fetch_tickets.main([])

        self.assertEqual(exit_code, 0)
        cli_main.assert_called_once_with()

    def test_main_prints_success_message_and_returns_zero_for_subcommands(self):
        stdout = io.StringIO()
        with patch("fetch_tickets._dispatch", return_value=True) as dispatch, patch("sys.stdout", new=stdout):
            exit_code = fetch_tickets.main(["check", "--retailer", "lidl", "--cookies-file", "lidl_cookies.json"])

        self.assertEqual(exit_code, 0)
        dispatch.assert_called_once()
        self.assertIn("✓ Check erfolgreich abgeschlossen!", stdout.getvalue())

    def test_main_prints_failure_message_and_returns_one_for_subcommands(self):
        stdout = io.StringIO()
        with patch("fetch_tickets._dispatch", return_value=False), patch("sys.stdout", new=stdout):
            exit_code = fetch_tickets.main(["update", "--retailer", "rewe"])

        self.assertEqual(exit_code, 1)
        self.assertIn("✗ Update fehlgeschlagen!", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

