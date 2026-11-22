import io
import unittest
from unittest.mock import patch

import cli.dm_menu as dm_menu
import cli.lidl_menu as lidl_menu
import cli.menu as main_menu
import cli.rewe_menu as rewe_menu
from cli.auth_prompts import prompt_auth_source, prompt_cookies_file
from cli.common_prompts import prompt_optional_value, prompt_with_default
from cli.dm_menu import show_dm_menu
from cli.lidl_menu import show_lidl_menu
from cli.rewe_menu import show_rewe_menu


class AuthPromptsTests(unittest.TestCase):
    def test_prompt_with_default_uses_default_when_empty(self):
        with patch("builtins.input", return_value=""):
            result = prompt_with_default("Pfad zur Cookie-Datei", "cookies.json")

        self.assertEqual(result, "cookies.json")

    def test_prompt_cookies_file_uses_default_when_empty(self):
        with patch("builtins.input", return_value=""):
            result = prompt_cookies_file("Pfad zur Cookie-Datei", "cookies.json")

        self.assertEqual(result, "cookies.json")

    def test_prompt_optional_value_returns_none_when_empty(self):
        with patch("builtins.input", return_value=""):
            result = prompt_optional_value("Optionaler Wert")

        self.assertIsNone(result)

    def test_prompt_auth_source_returns_browser_selection(self):
        with patch("builtins.input", side_effect=["2"]):
            result = prompt_auth_source("LIDL", "Cookie-Datei", "lidl_cookies.json")

        self.assertEqual(result, {"browser": "firefox"})


class CliMenuTests(unittest.TestCase):
    def test_main_menu_dispatches_to_lidl_and_continues(self):
        with patch("cli.menu.show_lidl_menu") as show_lidl_menu_mock:
            should_continue = main_menu._dispatch_main_menu_choice("1")

        self.assertTrue(should_continue)
        show_lidl_menu_mock.assert_called_once_with()

    def test_main_menu_returns_false_for_exit_choice(self):
        stdout = io.StringIO()
        with patch("sys.stdout", new=stdout):
            should_continue = main_menu._dispatch_main_menu_choice("5")

        self.assertFalse(should_continue)
        self.assertIn("Auf Wiedersehen!", stdout.getvalue())

    def test_lidl_menu_dispatch_runs_initial_and_closes_menu(self):
        with patch("cli.lidl_menu._run_lidl_initial") as run_initial:
            should_continue = lidl_menu._dispatch_lidl_menu_choice("1")

        self.assertFalse(should_continue)
        run_initial.assert_called_once_with()

    def test_lidl_menu_dispatch_runs_update_and_closes_menu(self):
        with patch("cli.lidl_menu._run_lidl_update") as run_update:
            should_continue = lidl_menu._dispatch_lidl_menu_choice("2")

        self.assertFalse(should_continue)
        run_update.assert_called_once_with()

    def test_rewe_menu_dispatch_prints_invalid_choice_and_keeps_menu_open(self):
        with patch("cli.rewe_menu.print_invalid_choice") as print_invalid_choice:
            should_continue = rewe_menu._dispatch_rewe_menu_choice("9")

        self.assertTrue(should_continue)
        print_invalid_choice.assert_called_once_with("1, 2, 3, 4 oder 5")

    def test_main_menu_dispatches_to_dm_and_continues(self):
        with patch("cli.menu.show_dm_menu") as show_dm_menu_mock:
            should_continue = main_menu._dispatch_main_menu_choice("3")

        self.assertTrue(should_continue)
        show_dm_menu_mock.assert_called_once_with()

    def test_dm_menu_dispatch_runs_initial_and_closes_menu(self):
        with patch("cli.dm_menu._run_dm_initial") as run_initial:
            should_continue = dm_menu._dispatch_dm_menu_choice("1")

        self.assertFalse(should_continue)
        run_initial.assert_called_once_with()

    def test_dm_menu_dispatch_runs_update_and_closes_menu(self):
        with patch("cli.dm_menu._run_dm_update") as run_update:
            should_continue = dm_menu._dispatch_dm_menu_choice("2")

        self.assertFalse(should_continue)
        run_update.assert_called_once_with()

    def test_dm_menu_dispatch_prints_invalid_choice_and_keeps_menu_open(self):
        with patch("cli.dm_menu.print_invalid_choice") as print_invalid_choice:
            should_continue = dm_menu._dispatch_dm_menu_choice("9")

        self.assertTrue(should_continue)
        print_invalid_choice.assert_called_once_with("1, 2, 3, 4 oder 5")

    def test_show_lidl_menu_prints_normalized_invalid_choice_message(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["9", "5"]), patch("sys.stdout", new=stdout):
            show_lidl_menu()

        self.assertIn("Ungültige Eingabe. Bitte wähle 1, 2, 3, 4 oder 5.", stdout.getvalue())

    def test_show_lidl_menu_runs_sync_with_prompted_auth(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["1", "", ""]), patch(
            "cli.lidl_menu.prompt_auth_source",
            return_value={"browser": "firefox"},
        ), patch("cli.lidl_menu.run_lidl_initial", return_value=True) as run_initial, patch(
            "sys.stdout", new=stdout
        ):
            show_lidl_menu()

        run_initial.assert_called_once_with(browser="firefox", country=None, output_dir="tmp/lidl")
        self.assertIn("✓ LIDL-Initial erfolgreich abgeschlossen!", stdout.getvalue())

    def test_show_lidl_menu_runs_update(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["2", ""]), patch(
            "cli.lidl_menu.run_lidl_update",
            return_value=True,
        ) as run_update, patch("sys.stdout", new=stdout):
            show_lidl_menu()

        run_update.assert_called_once_with(output_dir="tmp/lidl")
        self.assertIn("✓ LIDL-Update erfolgreich abgeschlossen!", stdout.getvalue())

    def test_show_lidl_menu_runs_check_with_prompted_cookie_file(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["4"]), patch(
            "cli.lidl_menu.prompt_cookies_file",
            return_value="lidl_cookies.json",
        ), patch("cli.lidl_menu.diagnose_lidl_cookie_file", return_value=True) as diagnose_lidl_cookie_file, patch(
            "sys.stdout", new=stdout
        ):
            show_lidl_menu()

        diagnose_lidl_cookie_file.assert_called_once_with("lidl_cookies.json")
        self.assertIn(
            "✓ LIDL-Cookie-Datei sieht grundsätzlich brauchbar aus!",
            stdout.getvalue(),
        )

    def test_show_lidl_menu_runs_json_export(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["3"]), patch(
            "cli.lidl_menu.run_retailer_export_json",
        ) as run_export, patch("sys.stdout", new=stdout):
            show_lidl_menu()

        run_export.assert_called_once_with("lidl", "lidl_receipts.json")

    def test_show_rewe_menu_runs_initial_with_prompted_auth(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["1", "tmp/rewe", ""]), patch(
            "cli.rewe_menu.prompt_auth_source",
            return_value={"cookies_file": "rewe_cookies.json"},
        ), patch("cli.rewe_menu.run_rewe_initial", return_value=True) as run_initial, patch(
            "sys.stdout", new=stdout
        ):
            show_rewe_menu()

        run_initial.assert_called_once_with(
            customer_id=None,
            output_dir="tmp/rewe",
            cookies_file="rewe_cookies.json",
        )
        self.assertIn("✓ REWE-Import erfolgreich abgeschlossen!", stdout.getvalue())

    def test_show_rewe_menu_runs_update_with_prompted_auth(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["2", "tmp/rewe"]), patch(
            "cli.rewe_menu.run_rewe_update", return_value=True
        ) as run_update, patch(
            "sys.stdout", new=stdout
        ):
            show_rewe_menu()

        run_update.assert_called_once_with(output_dir="tmp/rewe")
        self.assertIn("✓ REWE-Update erfolgreich abgeschlossen!", stdout.getvalue())

    def test_show_rewe_menu_runs_json_export(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["3"]), patch(
            "cli.rewe_menu.run_retailer_export_json",
        ) as run_export, patch("sys.stdout", new=stdout):
            show_rewe_menu()

        run_export.assert_called_once_with("rewe", "rewe_receipts.json")

    def test_show_rewe_menu_prints_normalized_invalid_choice_message(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["9", "5"]), patch("sys.stdout", new=stdout):
            show_rewe_menu()

        self.assertIn("Ungültige Eingabe. Bitte wähle 1, 2, 3, 4 oder 5.", stdout.getvalue())

    def test_show_dm_menu_runs_initial_with_prompted_auth(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["1", "tmp/dm"]), patch(
            "cli.dm_menu.prompt_auth_source",
            return_value={"cookies_file": "dm_cookies.json"},
        ), patch("cli.dm_menu.run_dm_initial", return_value=True) as run_initial, patch(
            "sys.stdout", new=stdout
        ):
            show_dm_menu()

        run_initial.assert_called_once_with(
            output_dir="tmp/dm",
            cookies_file="dm_cookies.json",
            browser=None,
        )
        self.assertIn("✓ dm-Import erfolgreich abgeschlossen!", stdout.getvalue())

    def test_show_dm_menu_runs_update(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["2", "tmp/dm"]), patch(
            "cli.dm_menu.run_dm_update", return_value=True
        ) as run_update, patch(
            "sys.stdout", new=stdout
        ):
            show_dm_menu()

        run_update.assert_called_once_with(output_dir="tmp/dm")
        self.assertIn("✓ dm-Update erfolgreich abgeschlossen!", stdout.getvalue())

    def test_show_dm_menu_runs_json_export(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["3"]), patch(
            "cli.dm_menu.run_retailer_export_json",
        ) as run_export, patch("sys.stdout", new=stdout):
            show_dm_menu()

        run_export.assert_called_once_with("dm", "dm_receipts.json")

    def test_show_dm_menu_runs_check_with_prompted_cookie_file(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["4"]), patch(
            "cli.dm_menu.prompt_cookies_file",
            return_value="dm_cookies.json",
        ), patch("cli.dm_menu.diagnose_dm_cookie_file", return_value=True) as diagnose_dm_cookie_file, patch(
            "sys.stdout", new=stdout
        ):
            show_dm_menu()

        diagnose_dm_cookie_file.assert_called_once_with("dm_cookies.json")
        self.assertIn(
            "✓ dm-Cookie-Datei sieht grundsätzlich brauchbar aus!",
            stdout.getvalue(),
        )

    def test_show_dm_menu_prints_normalized_invalid_choice_message(self):
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["9", "5"]), patch("sys.stdout", new=stdout):
            show_dm_menu()

        self.assertIn("Ungültige Eingabe. Bitte wähle 1, 2, 3, 4 oder 5.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

