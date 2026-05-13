import io
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import Mock, patch

import requests
import simplejson

import workflows.lidl_workflow as lidl_workflow
from result_types import PersistResult
from reporting.lidl_reporting import write_lidl_skipped_receipts_report
from workflows.lidl_workflow import _fetch_lidl_tickets, run_lidl_initial
from workflows.pipeline_types import ReceiptIssue, StageResult


class LidlWorkflowTests(unittest.TestCase):
    def test_lidl_workflow_public_api_only_exports_use_cases_and_diagnostics(self):
        self.assertEqual(
            lidl_workflow.__all__,
            [
                "run_lidl_initial",
                "run_lidl_update",
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
            records, issues = _fetch_lidl_tickets(cast(requests.Session, object()), ["receipt-1"])

        self.assertEqual(len(records), 1)
        self.assertEqual(issues, [])
        progress_display.assert_called_once_with(
            added_label="Abgerufen",
            items_label="Artikel",
        )
        final_state = progress_display.return_value.render.call_args_list[-1].args[0]
        self.assertEqual(final_state.items, 1)

    def test_fetch_lidl_tickets_maps_http_error_as_fetch_issue(self):
        response = Mock(status_code=401)
        http_error = requests.exceptions.HTTPError("boom")
        http_error.response = response

        with patch("workflows.lidl_workflow.ReceiptProgressDisplay"), patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            side_effect=http_error,
        ), patch("workflows.lidl_workflow.LidlConfig.REQUEST_DELAY", 0):
            records, issues = _fetch_lidl_tickets(cast(requests.Session, object()), ["receipt-1"])

        self.assertEqual(records, [])
        self.assertEqual([issue.reason for issue in issues], ["Nicht autorisiert (401)"])

    def test_fetch_lidl_tickets_maps_value_error_without_fetch_reason_kind(self):
        with patch("workflows.lidl_workflow.ReceiptProgressDisplay"), patch(
            "workflows.lidl_workflow.get_lidl_ticket",
            side_effect=ValueError("kaputt"),
        ), patch("workflows.lidl_workflow.LidlConfig.REQUEST_DELAY", 0):
            records, issues = _fetch_lidl_tickets(cast(requests.Session, object()), ["receipt-1"])

        self.assertEqual(records, [])
        self.assertEqual([issue.reason for issue in issues], ["kaputt"])


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
            report_payload = simplejson.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(written_path, report_path)
        self.assertEqual(report_payload["count"], 1)
        self.assertEqual(report_payload["skipped_receipts"], skipped_details)

    def test_run_lidl_initial_prints_skipped_receipts_and_report_path(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = set()
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
        self.assertEqual(store.find_existing_ids.call_args.kwargs["retailer"], "lidl")
        self.assertEqual(store.find_existing_ids.call_args.kwargs["file_path"], "lidl_receipts.json")
        self.assertIn("ℹ Übersprungene LIDL-Bons:", output)
        self.assertIn("✓ LIDL-Kassenbons importiert:", output)
        self.assertIn("23000987220230201728424", output)
        self.assertIn("Validatorfehler: items: keine Artikel erkannt", output)
        self.assertIn("tmp/skipped_receipts.json", output)

    def test_run_lidl_initial_passes_selected_write_backend_to_store_factory(self):
        store = Mock()
        store.find_existing_ids.return_value = set()

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

    def test_run_lidl_update_checks_recent_pages_and_reports_checked_pages(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = {"known-receipt"}
        session = object()

        with patch("workflows.lidl_workflow._setup_lidl_session", return_value=session), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=True,
        ), patch(
            "workflows.lidl_workflow._collect_lidl_receipt_ids",
            return_value=(["known-receipt", "new-receipt"], 3),
        ) as collect_receipt_ids, patch(
            "workflows.lidl_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.lidl_workflow._fetch_lidl_tickets",
            return_value=([], []),
        ), patch(
            "workflows.lidl_workflow.parse_receipts",
            return_value=StageResult(records=[], issues=[]),
        ), patch(
            "workflows.lidl_workflow.validate_receipts",
            return_value=StageResult(records=[], issues=[], total_items=0),
        ), patch(
            "workflows.lidl_workflow.persist_valid_receipts",
            return_value=PersistResult(created_count=1, updated_count=0, total_receipts=38),
        ), patch(
            "workflows.lidl_workflow.write_lidl_skipped_receipts_report",
            return_value=Path("tmp/skipped_receipts.json"),
        ), patch("sys.stdout", new=stdout):
            success = lidl_workflow.run_lidl_update(cookies_file="dummy.json")

        self.assertTrue(success)
        collect_receipt_ids.assert_called_once_with(session, lidl_workflow.LidlConfig.PAGES_TO_CHECK)
        self.assertIn("Geprüfte Seiten: 3", stdout.getvalue())

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

