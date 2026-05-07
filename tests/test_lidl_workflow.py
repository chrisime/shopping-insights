import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import workflows.lidl_workflow as lidl_workflow
from result_types import PersistResult, ReceiptStoreSnapshot
from reporting.lidl_reporting import write_lidl_skipped_receipts_report
from workflows.lidl_workflow import _fetch_lidl_tickets, run_lidl_check, run_lidl_initial
from workflows.pipeline_types import ReceiptIssue, StageResult


class LidlWorkflowTests(unittest.TestCase):
    def test_lidl_workflow_public_api_only_exports_use_cases_and_diagnostics(self):
        self.assertEqual(
            lidl_workflow.__all__,
            [
                "run_lidl_check",
                "run_lidl_initial",
                "run_lidl_update",
                "fetch_lidl_receipt_parse_result",
            ],
        )

    def test_fetch_lidl_tickets_uses_article_progress_count(self):
        ticket_html = (
            '<span class="article" data-art-id="1" data-art-description="Apfel" data-art-quantity="1" data-unit-price="1,99"></span>'
        )
        with patch("workflows.lidl_workflow.ReceiptProgressDisplay") as progress_display, patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            return_value={"htmlPrintedReceipt": ticket_html},
        ), patch("workflows.lidl_workflow.LidlConfig.REQUEST_DELAY", 0):
            records, issues = _fetch_lidl_tickets(object(), ["receipt-1"])

        self.assertEqual(len(records), 1)
        self.assertEqual(issues, [])
        progress_display.assert_called_once_with(
            added_label="Abgerufen",
            items_label="Artikel",
        )
        final_state = progress_display.return_value.render.call_args_list[-1].args[0]
        self.assertEqual(final_state.items, 1)

    def test_run_lidl_check_delegates_to_cookie_diagnostics(self):
        with patch(
            "workflows.lidl_workflow.diagnose_lidl_cookie_file",
            return_value=True,
        ) as diagnose:
            success = run_lidl_check("lidl_cookies.json")

        self.assertTrue(success)
        diagnose.assert_called_once_with("lidl_cookies.json")

    def test_write_lidl_skipped_receipts_report_writes_json_payload(self):
        skipped_details = [
            {
                "receipt_id": "23000987220230201728424",
                "reason": "Validatorfehler: items: keine Artikel erkannt",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "skipped_receipts.json"
            written_path = write_lidl_skipped_receipts_report(
                skipped_details,
                report_path=report_path,
            )
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(written_path, report_path)
        self.assertEqual(report_payload["count"], 1)
        self.assertEqual(report_payload["skipped_receipts"], skipped_details)

    def test_run_lidl_initial_prints_skipped_receipts_and_report_path(self):
        stdout = io.StringIO()
        store = Mock()
        store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
            existing_ids=set(),
            receipts=[],
            receipts_file="lidl_receipts.json",
        )
        with patch("workflows.lidl_workflow._setup_lidl_session", return_value=object()), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=True,
        ), patch(
            "workflows.lidl_workflow._collect_lidl_receipt_ids",
            return_value=(["23000987220230201728424"], 22),
        ), patch(
            "workflows.lidl_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.lidl_workflow._fetch_lidl_tickets",
            return_value=([], [ReceiptIssue("23000987220230201728424", "Validatorfehler: items: keine Artikel erkannt")]),
        ), patch(
            "workflows.lidl_workflow.parse_receipts",
            return_value=StageResult(records=[], issues=[]),
        ), patch(
            "workflows.lidl_workflow.validate_receipts",
            return_value=StageResult(records=[], issues=[]),
        ), patch(
            "workflows.lidl_workflow.persist_valid_receipts",
            return_value=PersistResult(created_count=0, updated_count=0, total_receipts=38),
        ), patch(
            "workflows.lidl_workflow.write_lidl_skipped_receipts_report",
            return_value=Path("tmp/skipped_receipts.json"),
        ), patch("sys.stdout", new=stdout):
            success = run_lidl_initial(cookies_file="dummy.json")

        output = stdout.getvalue()
        self.assertTrue(success)
        self.assertEqual(store.load_receipts_snapshot.call_args.kwargs["retailer"], "lidl")
        self.assertIn("ℹ Übersprungene LIDL-Bons:", output)
        self.assertIn("✓ LIDL-Kassenbons importiert:", output)
        self.assertIn("23000987220230201728424", output)
        self.assertIn("Validatorfehler: items: keine Artikel erkannt", output)
        self.assertIn("tmp/skipped_receipts.json", output)

    def test_run_lidl_initial_passes_selected_write_backend_to_store_factory(self):
        store = Mock()
        store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
            existing_ids=set(),
            receipts=[],
            receipts_file="lidl_receipts.json",
        )

        with patch("workflows.lidl_workflow._setup_lidl_session", return_value=object()), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=True,
        ), patch(
            "workflows.lidl_workflow._collect_lidl_receipt_ids",
            return_value=([], 1),
        ), patch(
            "workflows.lidl_workflow.create_receipt_store",
            return_value=store,
        ) as create_store, patch(
            "workflows.lidl_workflow._fetch_lidl_tickets",
            return_value=([], []),
        ), patch(
            "workflows.lidl_workflow.parse_receipts",
            return_value=StageResult(records=[], issues=[]),
        ), patch(
            "workflows.lidl_workflow.validate_receipts",
            return_value=StageResult(records=[], issues=[]),
        ), patch(
            "workflows.lidl_workflow.persist_valid_receipts",
            return_value=PersistResult(created_count=0, updated_count=0, total_receipts=0),
        ), patch(
            "workflows.lidl_workflow.write_lidl_skipped_receipts_report",
            return_value=Path("tmp/skipped_receipts.json"),
        ):
            success = lidl_workflow.run_lidl_initial(cookies_file="dummy.json", write_backend="json")

        self.assertTrue(success)
        create_store.assert_called_once_with("json")

    def test_run_lidl_initial_stops_when_api_test_fails(self):
        stdout = io.StringIO()

        with patch("workflows.lidl_workflow._setup_lidl_session", return_value=object()), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=False,
        ), patch("workflows.lidl_workflow._collect_lidl_receipt_ids") as collect_receipt_ids, patch(
            "sys.stdout", new=stdout
        ):
            success = run_lidl_initial(cookies_file="dummy.json")

        self.assertFalse(success)
        collect_receipt_ids.assert_not_called()

    def test_run_lidl_initial_fails_without_browser_or_cookie_file(self):
        stdout = io.StringIO()

        with patch("sys.stdout", new=stdout):
            success = run_lidl_initial()

        self.assertFalse(success)
        self.assertIn("✗ LIDL benötigt --cookies-file oder --browser.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

