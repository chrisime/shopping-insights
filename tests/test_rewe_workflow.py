import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import workflows.rewe_workflow as rewe_workflow
from result_types import PersistResult, ReceiptStoreSnapshot
from workflows.pipeline_types import ReceiptIssue, StageResult
from workflows.rewe_workflow import (
    _filter_new_rewe_pdf_paths,
    import_rewe_receipts_from_pdfs,
    run_rewe_initial,
    run_rewe_update,
)


class ReweWorkflowTests(unittest.TestCase):
    def test_rewe_workflow_public_api_contains_only_public_entrypoints(self):
        self.assertEqual(
            rewe_workflow.__all__,
            [
                "run_rewe_initial",
                "run_rewe_update",
                "run_rewe_check",
                "import_rewe_receipts_from_pdfs",
                "parse_rewe_receipt_pdf_with_result",
            ],
        )

    def test_filter_new_rewe_pdf_paths_keeps_only_unknown_receipt_ids(self):
        pdf_paths = [Path("known.pdf"), Path("new.pdf"), Path("broken.pdf")]

        def fake_metadata(pdf_path: Path):
            if pdf_path.name == "known.pdf":
                return {"id": "known-id"}
            if pdf_path.name == "new.pdf":
                return {"id": "new-id"}
            raise ValueError("kaputt")

        with patch(
            "workflows.rewe_workflow.ReceiptProgressDisplay",
        ) as progress_display, patch(
            "workflows.rewe_workflow.extract_rewe_receipt_metadata_from_pdf",
            side_effect=fake_metadata,
        ):
            new_paths, issues = _filter_new_rewe_pdf_paths(pdf_paths, ["known-id"])

        self.assertEqual(new_paths, [Path("new.pdf")])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].source_id, "broken.pdf")
        self.assertIn("Delta-Prüfung", issues[0].reason)
        progress_display.return_value.render.assert_called()
        progress_display.return_value.close.assert_called_once_with()

    def test_import_rewe_receipts_prints_skipped_file_and_reason(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_dir = Path(tmp_dir)
            pdf_path = pdf_dir / "skip-me.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            stdout = io.StringIO()
            fake_store = Mock()
            fake_store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
                existing_ids=set(),
                receipts=[],
                receipts_file="rewe_receipts.json",
            )
            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow.parse_receipts",
                return_value=StageResult(
                    records=[],
                    issues=[ReceiptIssue("skip-me.pdf", "Validatorfehler: payment_methods fehlen", detail_key="file")],
                ),
            ), patch(
                "workflows.rewe_workflow.validate_receipts",
                return_value=StageResult(records=[], issues=[]),
            ), patch(
                "workflows.rewe_workflow.persist_valid_receipts",
                return_value=PersistResult(created_count=0, updated_count=0, total_receipts=203),
            ), patch("sys.stdout", new=stdout):
                imported_count, skipped_count, total_receipts = import_rewe_receipts_from_pdfs(pdf_dir)

            report_path = pdf_dir.parent / "skipped_receipts.json"
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))

        output = stdout.getvalue()
        self.assertEqual(imported_count, 0)
        self.assertEqual(skipped_count, 1)
        self.assertEqual(total_receipts, 203)
        self.assertIn("ℹ Übersprungene REWE-Bons:", output)
        self.assertIn("skip-me.pdf", output)
        self.assertIn("Validatorfehler: payment_methods fehlen", output)
        self.assertIn("skipped_receipts.json", output)
        self.assertTrue(report_path.exists())
        self.assertEqual(report_payload["count"], 1)
        self.assertEqual(
            report_payload["skipped_receipts"],
            [{"file": "skip-me.pdf", "reason": "Validatorfehler: payment_methods fehlen"}],
        )

    def test_run_rewe_initial_stops_when_api_test_fails(self):
        with patch("workflows.rewe_workflow._load_rewe_session",
            return_value=object(),
        ), patch(
            "workflows.rewe_workflow.resolve_rewe_customer_id",
            return_value="customer-1",
        ), patch(
            "workflows.rewe_workflow.test_rewe_session",
            return_value=False,
        ), patch("workflows.rewe_workflow.download_receipts_zip") as download_zip:
            success = run_rewe_initial(cookies_file="rewe_cookies.json")

        self.assertFalse(success)
        download_zip.assert_not_called()

    def test_run_rewe_update_imports_only_new_receipts_from_downloaded_zip(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pdf_dir = output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "known.pdf").write_bytes(b"%PDF-1.4\n")
            (pdf_dir / "new.pdf").write_bytes(b"%PDF-1.4\n")

            def fake_metadata(pdf_path: Path):
                if pdf_path.name == "known.pdf":
                    return {"id": "known-id"}
                return {"id": "new-id"}

            fake_store = Mock()
            fake_store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
                existing_ids={"known-id"},
                receipts=[{"id": "known-id"}],
                receipts_file="rewe_receipts.json",
            )

            with patch("workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow.extract_rewe_receipt_metadata_from_pdf",
                side_effect=fake_metadata,
            ), patch(
                "workflows.rewe_workflow.parse_receipts",
                return_value=StageResult(records=[], issues=[]),
            ) as parse_receipts, patch(
                "workflows.rewe_workflow.validate_receipts",
                return_value=StageResult(records=[], issues=[]),
            ), patch(
                "workflows.rewe_workflow.persist_valid_receipts",
                return_value=PersistResult(created_count=1, updated_count=0, total_receipts=11),
            ):
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertTrue(success)
        raw_records = parse_receipts.call_args.args[0]
        self.assertEqual([record.source_id for record in raw_records], ["new.pdf"])

    def test_run_rewe_update_reports_total_items_from_pipeline_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pdf_dir = output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "new.pdf").write_bytes(b"%PDF-1.4\n")

            stdout = io.StringIO()
            fake_store = Mock()
            fake_store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
                existing_ids=set(),
                receipts=[],
                receipts_file="rewe_receipts.json",
            )
            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow.extract_rewe_receipt_metadata_from_pdf",
                return_value={"id": "new-id"},
            ), patch(
                "workflows.rewe_workflow.parse_receipts",
                return_value=StageResult(records=[], issues=[]),
            ), patch(
                "workflows.rewe_workflow.validate_receipts",
                return_value=StageResult(records=[], issues=[], total_items=7),
            ), patch(
                "workflows.rewe_workflow.persist_valid_receipts",
                return_value=PersistResult(created_count=1, updated_count=0, total_receipts=11),
            ), patch("sys.stdout", new=stdout):
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertTrue(success)
        self.assertIn("7 Artikel", stdout.getvalue())

    def test_run_rewe_update_returns_success_without_reparsing_when_all_receipts_are_known(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pdf_dir = output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "known.pdf").write_bytes(b"%PDF-1.4\n")
            fake_store = Mock()
            fake_store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
                existing_ids={"known-id"},
                receipts=[{"id": "known-id"}],
                receipts_file="rewe_receipts.json",
            )

            with patch("workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow.extract_rewe_receipt_metadata_from_pdf",
                return_value={"id": "known-id"},
            ), patch("workflows.rewe_workflow.parse_receipts") as parse_receipts, patch(
                "workflows.rewe_workflow.persist_valid_receipts",
            ) as persist_receipts:
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertTrue(success)
        parse_receipts.assert_not_called()
        persist_receipts.assert_not_called()

    def test_run_rewe_update_fails_when_no_local_pdfs_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            fake_store = Mock()
            fake_store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
                existing_ids=set(),
                receipts=[],
                receipts_file="rewe_receipts.json",
            )

            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ):
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertFalse(success)

    def test_run_rewe_update_passes_selected_write_backend_to_store_factory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            fake_store = Mock()
            fake_store.load_receipts_snapshot.return_value = ReceiptStoreSnapshot(
                existing_ids=set(),
                receipts=[],
                receipts_file="rewe_receipts.json",
            )

            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ) as create_store:
                success = run_rewe_update(output_dir=str(output_dir), write_backend="json")

        self.assertFalse(success)
        create_store.assert_called_once_with("json")


if __name__ == "__main__":
    unittest.main()

