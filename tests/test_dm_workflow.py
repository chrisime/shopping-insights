from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import workflows.dm_workflow as dm_workflow
from result_types import PersistResult, WorkflowSummary
from workflows.dm_workflow import run_dm_initial, run_dm_update
from workflows.pipeline_types import WorkflowResult

MARKET_PURCHASE = {
    "id": "c51ccff9-13e9-47a0-a4f7-2d0c7dd03e91_2026",
    "purchaseType": "MARKET",
    "ebonData": {"followUpOrder": False},
}
ONLINE_PURCHASE = {
    "id": "online-order-1_2026",
    "purchaseType": "ONLINE",
}


class DmWorkflowPublicApiTests(unittest.TestCase):
    def test_public_api_only_exports_use_cases(self):
        self.assertEqual(
            dm_workflow.__all__,
            ["run_dm_initial", "run_dm_update"],
        )


class DmMarketFilterTests(unittest.TestCase):
    def test_is_market_ebon_accepts_market_with_ebon_data(self):
        self.assertTrue(dm_workflow._is_market_ebon(MARKET_PURCHASE))

    def test_is_market_ebon_rejects_online_order(self):
        self.assertFalse(dm_workflow._is_market_ebon(ONLINE_PURCHASE))

    def test_is_market_ebon_rejects_market_without_ebon_data(self):
        purchase = {"id": "x_2026", "purchaseType": "MARKET"}
        self.assertFalse(dm_workflow._is_market_ebon(purchase))


class DmLoadPayloadTests(unittest.TestCase):
    def test_load_payload_returns_json_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "abc_2026.json"
            source_path.write_text(
                '{"id":"abc_2026","date":"2026-01-07","totalAmount":5.28}',
                encoding="utf-8",
            )
            payload = dm_workflow._load_dm_ebon_payload(source_path)
        self.assertEqual(payload["id"], "abc_2026")
        self.assertEqual(payload["totalAmount"], 5.28)

    def test_load_payload_raises_on_non_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "bad.json"
            source_path.write_text('["not","a","dict"]', encoding="utf-8")
            with self.assertRaises(ValueError):
                dm_workflow._load_dm_ebon_payload(source_path)


class RunDmInitialTests(unittest.TestCase):
    def _workflow_result(self, processed=0):
        return WorkflowResult(
            success=True,
            summary=WorkflowSummary(
                retailer="dm",
                processed_count=processed,
                skipped_count=0,
                total_receipts=processed,
                receipts_file="shopping_receipts.sqlite",
                total_items=0,
            ),
            skipped_issues=[],
            skipped_report_path=None,
        )

    def test_run_dm_initial_downloads_only_market_ebons(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = set()
        api_session = object()

        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.dm_workflow._prepare_dm_session",
            return_value=(api_session, Mock()),
        ), patch(
            "workflows.dm_workflow.collect_dm_purchases",
            return_value=[MARKET_PURCHASE, ONLINE_PURCHASE],
        ), patch(
            "workflows.dm_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.dm_workflow._download_dm_ebons",
        ) as download_ebons, patch(
            "workflows.dm_workflow.import_local_sources",
            return_value=self._workflow_result(),
        ), patch("sys.stdout", new=stdout):
            success = run_dm_initial(cookies_file="dummy.json", output_dir=tmp_dir)

        self.assertTrue(success)
        self.assertEqual(store.find_existing_ids.call_args.kwargs["retailer"], "dm")
        download_ebons.assert_called_once()
        download_ebons_args = download_ebons.call_args.args
        self.assertEqual(download_ebons_args[1][0]["id"], MARKET_PURCHASE["id"])
        self.assertIn("Online-Bestellungen werden nicht als Beleg importiert.", stdout.getvalue())

    def test_run_dm_initial_skips_already_persisted_ebons(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = {MARKET_PURCHASE["id"]}

        with patch(
            "workflows.dm_workflow._prepare_dm_session",
            return_value=(object(), Mock()),
        ), patch(
            "workflows.dm_workflow.collect_dm_purchases",
            return_value=[MARKET_PURCHASE],
        ), patch(
            "workflows.dm_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.dm_workflow._download_dm_ebons",
        ) as download_ebons, patch(
            "workflows.dm_workflow.import_local_sources",
            return_value=self._workflow_result(),
        ), patch("sys.stdout", new=stdout):
            success = run_dm_initial(cookies_file="dummy.json")

        self.assertTrue(success)
        download_ebons.assert_not_called()

    def test_run_dm_initial_stops_when_session_preparation_fails(self):
        stdout = io.StringIO()
        with patch(
            "workflows.dm_workflow._prepare_dm_session",
            return_value=None,
        ), patch(
            "workflows.dm_workflow.collect_dm_purchases",
        ) as collect_purchases, patch("sys.stdout", new=stdout):
            success = run_dm_initial(cookies_file="dummy.json")

        self.assertFalse(success)
        collect_purchases.assert_not_called()

    def test_run_dm_initial_fails_without_browser_or_cookie_file(self):
        stdout = io.StringIO()
        with patch("sys.stdout", new=stdout):
            success = run_dm_initial()
        self.assertFalse(success)
        self.assertIn("✗ dm benötigt --cookies-file oder --browser.", stdout.getvalue())


class RunDmUpdateTests(unittest.TestCase):
    def _write_ebon_json(self, directory: Path) -> None:
        ebons_dir = directory / "ebons"
        ebons_dir.mkdir(parents=True, exist_ok=True)
        (ebons_dir / "abc_2026.json").write_text(
            '{"id":"abc_2026","date":"2026-01-07","totalAmount":5.28,"bonItems":[{"dan":"1446511"}]}',
            encoding="utf-8",
        )

    def test_run_dm_update_imports_existing_jsons(self):
        store = Mock()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.dm_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.dm_workflow.import_local_sources",
            return_value=WorkflowResult(
                success=True,
                summary=WorkflowSummary(
                    retailer="dm",
                    processed_count=1,
                    skipped_count=0,
                    total_receipts=1,
                    receipts_file="shopping_receipts.sqlite",
                    total_items=1,
                ),
                skipped_issues=[],
                skipped_report_path=None,
            ),
        ) as import_pipeline:
            self._write_ebon_json(Path(tmp_dir))
            store.persist_receipts.return_value = PersistResult(
                created_count=1, updated_count=0, total_receipts=1
            )
            success = run_dm_update(output_dir=tmp_dir)

        self.assertTrue(success)
        import_pipeline.assert_called_once()
        import_kwargs = import_pipeline.call_args.kwargs
        self.assertEqual(import_kwargs["retailer"], "dm")
        self.assertEqual(
            [p.name for p in import_kwargs["source_paths"]],
            ["abc_2026.json"],
        )

    def test_run_dm_update_fails_without_existing_jsons(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.dm_workflow.create_receipt_store",
            return_value=Mock(),
        ), patch("sys.stdout", new=stdout):
            success = run_dm_update(output_dir=tmp_dir)
        self.assertFalse(success)
        self.assertIn("Keine dm-eBon-JSONs zum Importieren gefunden", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()