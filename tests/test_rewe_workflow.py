import io
import simplejson
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from config import ReweConfig
from config import storage_config
import workflows.rewe_workflow as rewe_workflow
from result_types import PersistResult
from workflows.pipeline_types import ReceiptIssue, StageResult, WorkflowResult
from workflows.rewe_workflow import run_rewe_initial, run_rewe_update


def _import_rewe_receipts_from_pdfs(
    pdf_dir: Path,
) -> tuple[int, int, int]:
    store = rewe_workflow.create_receipt_store()
    workflow_result = rewe_workflow._run_rewe_pdf_import_pipeline(
        pdf_dir,
        store=store,
    )
    return (
        workflow_result.summary.processed_count,
        workflow_result.summary.skipped_count,
        workflow_result.summary.total_receipts,
    )


class ReweWorkflowTests(unittest.TestCase):
    def test_rewe_workflow_public_api_contains_only_public_entrypoints(self):
        self.assertEqual(
            rewe_workflow.__all__,
            [
                "run_rewe_initial",
                "run_rewe_update",
            ],
        )


    def test_import_rewe_receipts_prints_skipped_file_and_reason(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_dir = Path(tmp_dir)
            pdf_path = pdf_dir / "skip-me.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n")

            stdout = io.StringIO()
            fake_store = Mock()
            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.import_pipeline.parse_receipts",
                return_value=StageResult(
                    records=[],
                    issues=[ReceiptIssue("skip-me.pdf", "Validatorfehler: payment_methods fehlen", detail_key="file")],
                ),
            ), patch(
                "workflows.import_pipeline.validate_receipts",
                return_value=StageResult(records=[], issues=[]),
            ), patch("sys.stdout", new=stdout):
                fake_store.persist_receipts.return_value = PersistResult(created_count=0, updated_count=0, total_receipts=203)
                imported_count, skipped_count, total_receipts = _import_rewe_receipts_from_pdfs(pdf_dir)

            report_path = pdf_dir.parent / ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE
            report_payload = simplejson.loads(report_path.read_text(encoding="utf-8"))

        output = stdout.getvalue()
        self.assertEqual(imported_count, 0)
        self.assertEqual(skipped_count, 1)
        self.assertEqual(total_receipts, 203)
        self.assertIn("ℹ Übersprungene REWE-Bons:", output)
        self.assertIn("skip-me.pdf", output)
        self.assertIn("Validatorfehler: payment_methods fehlen", output)
        self.assertIn(ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE, output)
        self.assertTrue(report_path.exists())
        self.assertEqual(report_payload["count"], 1)
        self.assertEqual(
            report_payload["skipped_receipts"],
            [{"file": "skip-me.pdf", "reason": "Validatorfehler: payment_methods fehlen"}],
        )

    def test_run_rewe_initial_stops_when_api_test_fails(self):
        with patch("workflows.rewe_workflow.setup_session",
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

    def test_run_rewe_update_imports_all_local_receipts_from_downloaded_pdfs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pdf_dir = output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "first.pdf").write_bytes(b"%PDF-1.4\n")
            (pdf_dir / "second.pdf").write_bytes(b"%PDF-1.4\n")

            fake_store = Mock()

            with patch("workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow._ReweImportPipeline.run",
                return_value=WorkflowResult(
                    success=True,
                    summary=rewe_workflow.WorkflowSummary(
                        retailer=rewe_workflow.RETAILER_REWE,
                        processed_count=1,
                        skipped_count=0,
                        total_receipts=11,
                        receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
                        total_items=0,
                    ),
                    skipped_issues=[],
                    skipped_report_path=pdf_dir.parent / ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE,
                ),
            ) as import_pipeline:
                fake_store.persist_receipts.return_value = PersistResult(created_count=1, updated_count=0, total_receipts=11)
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertTrue(success)
        fake_store.find_existing_ids.assert_not_called()
        self.assertEqual([path.name for path in import_pipeline.call_args.kwargs["source_paths"]], ["first.pdf", "second.pdf"])

    def test_run_rewe_update_reports_total_items_from_pipeline_validation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pdf_dir = output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "new.pdf").write_bytes(b"%PDF-1.4\n")

            stdout = io.StringIO()
            fake_store = Mock()
            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow._ReweImportPipeline.run",
                return_value=WorkflowResult(
                    success=True,
                    summary=rewe_workflow.WorkflowSummary(
                        retailer=rewe_workflow.RETAILER_REWE,
                        processed_count=1,
                        skipped_count=0,
                        total_receipts=11,
                        receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
                        total_items=7,
                    ),
                    skipped_issues=[],
                    skipped_report_path=pdf_dir.parent / ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE,
                ),
            ), patch("sys.stdout", new=stdout):
                fake_store.persist_receipts.return_value = PersistResult(created_count=1, updated_count=0, total_receipts=11)
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertTrue(success)
        self.assertIn("7 Artikel", stdout.getvalue())

    def test_run_rewe_update_reimports_even_previously_known_local_receipts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            pdf_dir = output_dir / "pdfs"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "known.pdf").write_bytes(b"%PDF-1.4\n")
            fake_store = Mock()

            with patch("workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ), patch(
                "workflows.rewe_workflow._ReweImportPipeline.run",
                return_value=WorkflowResult(
                    success=True,
                    summary=rewe_workflow.WorkflowSummary(
                        retailer=rewe_workflow.RETAILER_REWE,
                        processed_count=1,
                        skipped_count=0,
                        total_receipts=1,
                        receipts_file=storage_config.SQLITE_RECEIPTS_DB_FILE,
                        total_items=0,
                    ),
                    skipped_issues=[],
                    skipped_report_path=pdf_dir.parent / ReweConfig.SKIPPED_RECEIPTS_REPORT_FILE,
                ),
            ) as import_pipeline:
                fake_store.persist_receipts.return_value = PersistResult(created_count=0, updated_count=1, total_receipts=1)
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertTrue(success)
        fake_store.find_existing_ids.assert_not_called()
        import_pipeline.assert_called_once()

    def test_run_rewe_update_fails_when_no_local_pdfs_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            fake_store = Mock()

            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ):
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertFalse(success)

    def test_run_rewe_update_uses_default_store_factory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            fake_store = Mock()

            with patch(
                "workflows.rewe_workflow.create_receipt_store",
                return_value=fake_store,
            ) as create_store:
                success = run_rewe_update(output_dir=str(output_dir))

        self.assertFalse(success)
        create_store.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
