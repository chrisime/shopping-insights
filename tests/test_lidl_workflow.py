from __future__ import annotations

import io
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

import workflows.lidl_workflow as lidl_workflow
from result_types import PersistResult, WorkflowSummary
from shared.lidl_ticket_dto import LidlTicketDTO
from workflows.lidl_workflow import run_lidl_initial
from workflows.pipeline_types import ReceiptIssue, WorkflowResult


@dataclass(frozen=True)
class LidlTicketPreview:
    """Minimal ticket data from the Lidl listing page (test helper)."""

    id: str
    has_html_receipt: bool

    @staticmethod
    def from_api_response(ticket_data: Dict[str, Any]) -> Optional[LidlTicketPreview]:
        """Extract preview data from a page item, handling nested 'ticket' key."""
        if isinstance(ticket_data, dict) and "ticket" in ticket_data:
            inner_ticket = ticket_data["ticket"]
        else:
            inner_ticket = ticket_data

        if not isinstance(inner_ticket, dict):
            return None

        receipt_id = str(inner_ticket.get("id") or "")
        has_html = bool(inner_ticket.get("isHtml", False))

        if not receipt_id:
            return None

        return LidlTicketPreview(id=receipt_id, has_html_receipt=has_html)


def _extract_receipt_ids_from_tickets(raw_tickets: List[Dict[str, object]]) -> List[str]:
    """Extract receipt ids for tickets that have an HTML receipt representation (test helper)."""
    return [
        preview.id
        for ticket in raw_tickets
        if (preview := LidlTicketPreview.from_api_response(ticket)) is not None and preview.has_html_receipt
    ]


class LidlWorkflowTests(unittest.TestCase):
    def test_lidl_workflow_public_api_only_exports_use_cases_and_diagnostics(self):
        self.assertEqual(
            lidl_workflow.__all__,
            [
                "run_lidl_initial",
                "run_lidl_update",
            ],
        )


    def test_run_lidl_initial_prints_shared_import_summary(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = set()
        session = object()
        result = WorkflowResult(
            success=True,
            summary=WorkflowSummary(
                retailer="lidl",
                processed_count=0,
                skipped_count=1,
                total_receipts=38,
                receipts_file="shopping_receipts.sqlite",
                total_items=0,
                checked_pages=22,
            ),
            skipped_issues=[ReceiptIssue("23000987220230201728424", "Validatorfehler: items: keine Artikel erkannt")],
            skipped_report_path=Path("tmp/skipped_receipts.json"),
        )

        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.lidl_workflow.setup_session", return_value=session
        ), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=True,
        ), patch(
            "workflows.lidl_workflow.collect_lidl_receipt_ids",
            return_value=(["23000987220230201728424"], 22),
        ), patch(
            "workflows.lidl_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.lidl_workflow._download_lidl_tickets",
        ) as download_tickets, patch(
            "workflows.lidl_workflow._LidlImportPipeline.run",
            return_value=result,
        ) as import_pipeline, patch("sys.stdout", new=stdout):
            success = run_lidl_initial(cookies_file="dummy.json", output_dir=tmp_dir)

        output = stdout.getvalue()
        self.assertTrue(success)
        self.assertEqual(store.find_existing_ids.call_args.kwargs["retailer"], "lidl")
        expected_tickets_dir = Path(tmp_dir) / "tickets"
        download_tickets.assert_called_once_with(session, ["23000987220230201728424"], expected_tickets_dir)
        import_pipeline.assert_called_once()
        import_kwargs = import_pipeline.call_args.kwargs
        self.assertEqual(import_kwargs["source_dir"], expected_tickets_dir)
        self.assertEqual(import_kwargs["source_paths"], [])
        self.assertEqual(import_kwargs["retailer"], "lidl")
        self.assertEqual(import_kwargs["receipts_file"], "shopping_receipts.sqlite")
        self.assertEqual(import_kwargs["store"], store)
        self.assertEqual(import_kwargs["checked_pages"], 22)
        self.assertIn("LIDL-Kassenbons importiert:", output)
        self.assertIn("Geprüfte Seiten: 22", output)

    def test_run_lidl_initial_uses_default_store_factory(self):
        store = Mock()
        store.find_existing_ids.return_value = set()

        with patch("workflows.lidl_workflow.setup_session", return_value=object()), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=True,
        ), patch(
            "workflows.lidl_workflow.collect_lidl_receipt_ids",
            return_value=([], 1),
        ), patch(
            "workflows.lidl_workflow.create_receipt_store",
            return_value=store,
        ) as create_store, patch(
            "workflows.lidl_workflow._LidlImportPipeline.run",
            return_value=WorkflowResult(
                success=True,
                summary=WorkflowSummary(
                    retailer="lidl",
                    processed_count=0,
                    skipped_count=0,
                    total_receipts=0,
                    receipts_file="shopping_receipts.sqlite",
                    total_items=0,
                    checked_pages=1,
                ),
                skipped_issues=[],
                skipped_report_path=None,
            ),
        ):
            store.persist_receipts.return_value = PersistResult(created_count=0, updated_count=0, total_receipts=0)
            success = lidl_workflow.run_lidl_initial(cookies_file="dummy.json")

        self.assertTrue(success)
        create_store.assert_called_once_with()

    def test_run_lidl_initial_checks_all_pages_and_processes_only_new_receipts(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = {"known-receipt", "already-imported"}
        session = object()

        with patch("workflows.lidl_workflow.setup_session", return_value=session), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=True,
        ), patch(
            "workflows.lidl_workflow.collect_lidl_receipt_ids",
            return_value=(
                [
                    "known-receipt",
                    "new-receipt",
                    "already-imported",
                ],
                3,
            ),
        ) as collect_receipt_ids, patch(
            "workflows.lidl_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.lidl_workflow._download_lidl_tickets",
        ) as download_tickets, patch(
            "workflows.lidl_workflow._LidlImportPipeline.run",
            return_value=WorkflowResult(
                success=True,
                summary=WorkflowSummary(
                    retailer="lidl",
                    processed_count=1,
                    skipped_count=0,
                    total_receipts=38,
                    receipts_file="shopping_receipts.sqlite",
                    total_items=0,
                    checked_pages=3,
                ),
                skipped_issues=[],
                skipped_report_path=Path("tmp/skipped_receipts.json"),
            ),
        ), patch("sys.stdout", new=stdout):
            store.persist_receipts.return_value = PersistResult(created_count=1, updated_count=0, total_receipts=38)
            success = run_lidl_initial(cookies_file="dummy.json")

        self.assertTrue(success)
        collect_receipt_ids.assert_called_once_with(session)
        download_tickets.assert_called_once_with(session, ["new-receipt"], Path("tmp/lidl/tickets"))
        self.assertIn("Geprüfte Seiten: 3", stdout.getvalue())

    def test_lidl_skipped_output_handles_file_detail_key_fallback(self):
        stdout = io.StringIO()

        with patch("sys.stdout", new=stdout):
            lidl_workflow._LidlImportPipeline().print_skipped_receipts(
                [{"file": "receipt-1.json", "reason": "Validatorfehler: items fehlen"}],
                report_path=None,
            )

        output = stdout.getvalue()
        self.assertIn("Übersprungene LIDL-Bons", output)
        self.assertIn("receipt-1.json", output)
        self.assertIn("Validatorfehler: items fehlen", output)

    def test_lidl_import_pipeline_load_payload_returns_ticket_dto(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "receipt-1.json"
            source_path.write_text(
                '{"id":"receipt-1","date":"2024-01-02","htmlPrintedReceipt":"<html></html>","store":{"name":"Lidl"}}',
                encoding="utf-8",
            )

            payload = lidl_workflow._LidlImportPipeline().load_payload(source_path)

        self.assertIsInstance(payload, LidlTicketDTO)
        self.assertEqual(payload.id, "receipt-1")


    def test_extract_receipt_ids_keeps_only_tickets_with_html(self):
        base_ticket = {
            "id": "receipt-1",
            "date": "28.08.2024",
            "isHtml": True,
            "totalAmount": 19.23,
            "store": {
                "id": "store-1",
                "name": "Lidl Fürth",
            },
        }

        receipt_ids = _extract_receipt_ids_from_tickets(
            [
                {
                    **base_ticket,
                    "page": 1,
                    "uiBadge": "neu",
                },
                {
                    **base_ticket,
                    "id": "receipt-2",
                    "isHtml": False,
                },
            ]
        )

        self.assertEqual(receipt_ids, ["receipt-1"])

    def test_filter_new_lidl_receipt_ids_skips_already_persisted_receipts(self):
        receipt_ids = lidl_workflow._filter_new_lidl_receipt_ids(
            ["known-receipt", "new-receipt", "known-receipt", "new-receipt", "newer-receipt"],
            {"known-receipt"},
        )

        self.assertEqual(receipt_ids, ["new-receipt", "newer-receipt"])

    def test_run_lidl_initial_stops_when_api_test_fails(self):
        stdout = io.StringIO()

        with patch("workflows.lidl_workflow.setup_session", return_value=object()), patch(
            "workflows.lidl_workflow.test_lidl_session",
            return_value=False,
        ), patch("workflows.lidl_workflow.collect_lidl_receipt_ids") as collect_receipt_ids, patch(
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
