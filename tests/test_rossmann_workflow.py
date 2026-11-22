from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import workflows.rossmann_workflow as rossmann_workflow
from auth.rossmann_auth import RossmannAccount
from result_types import PersistResult, WorkflowSummary
from workflows.pipeline_types import WorkflowResult
from workflows.rossmann_workflow import run_rossmann_initial, run_rossmann_update


SAMPLE_LIST_ENTRY = {"id": "7ca5482b-73ab-4907-89fd-afc6214a14b6"}
RECEIPT_LIST_ENTRY = SAMPLE_LIST_ENTRY


class RossmannWorkflowPublicApiTests(unittest.TestCase):
    def test_public_api_only_exports_use_cases(self):
        self.assertEqual(
            rossmann_workflow.__all__,
            ["run_rossmann_initial", "run_rossmann_update"],
        )


class RossmannLoadPayloadTests(unittest.TestCase):
    def test_load_payload_returns_json_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "abc.json"
            source_path.write_text('{"id":"abc","head":{"date":"2026-09-01T00:00:00Z"}}', encoding="utf-8")
            payload = rossmann_workflow._load_rossmann_receipt_payload(source_path)
        self.assertEqual(payload["id"], "abc")

    def test_load_payload_raises_on_non_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "bad.json"
            source_path.write_text('["not","a","dict"]', encoding="utf-8")
            with self.assertRaises(ValueError):
                rossmann_workflow._load_rossmann_receipt_payload(source_path)


class BuildAccountTests(unittest.TestCase):
    def test_from_cli_args(self):
        account = rossmann_workflow._build_account("acct-1", "hsh-1", None)
        if account is None:
            self.fail("expected account")
        self.assertEqual(account.account_id, "acct-1")
        self.assertEqual(account.account_hash, "hsh-1")

    def test_from_cookie_file(self):
        import json

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "ross.json"
            path.write_text(json.dumps({"accountId": "acct-2", "accountHash": "hsh-2"}), encoding="utf-8")
            account = rossmann_workflow._build_account(None, None, str(path))
        if account is None:
            self.fail("expected account")
        self.assertEqual(account.account_id, "acct-2")


class RunRossmannInitialTests(unittest.TestCase):
    def _workflow_result(self):
        return WorkflowResult(
            success=True,
            summary=WorkflowSummary(
                retailer="rossmann",
                processed_count=0,
                skipped_count=0,
                total_receipts=0,
                receipts_file="shopping_receipts.sqlite",
                total_items=0,
            ),
            skipped_issues=[],
            skipped_report_path=None,
        )

    def test_run_rossmann_initial_with_account_and_download(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = set()

        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.rossmann_workflow._prepare_rossmann_session",
            return_value=(object(), Mock()),
        ), patch(
            "workflows.rossmann_workflow.collect_rossmann_receipts",
            return_value=[RECEIPT_LIST_ENTRY],
        ), patch(
            "workflows.rossmann_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.rossmann_workflow._download_rossmann_receipts",
            return_value=True,
        ) as download_receipts, patch(
            "workflows.rossmann_workflow.import_local_sources",
            return_value=self._workflow_result(),
        ), patch("sys.stdout", new=stdout):
            success = run_rossmann_initial(
                cookies_file="dummy.json",
                account_id="acct-1",
                account_hash="hsh-1",
                output_dir=tmp_dir,
            )

        self.assertTrue(success)
        self.assertEqual(store.find_existing_ids.call_args.kwargs["retailer"], "rossmann")
        download_receipts.assert_called_once()

    def test_rossmann_initial_fails_when_session_preparation_fails(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.rossmann_workflow._prepare_rossmann_session",
            return_value=None,
        ), patch(
            "workflows.rossmann_workflow.collect_rossmann_receipts",
        ) as collect, patch(
            "workflows.rossmann_workflow.create_receipt_store", return_value=Mock(),
        ), patch("sys.stdout", new=stdout):
            success = run_rossmann_initial(
                cookies_file="dummy.json",
                account_id="acct-1",
                account_hash="hsh-1",
                output_dir=tmp_dir,
            )
        self.assertFalse(success)
        collect.assert_not_called()

    def test_rossmann_initial_prompts_login_when_no_account(self):
        stdout = io.StringIO()
        store = Mock()
        store.find_existing_ids.return_value = set()

        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.rossmann_workflow.prompt_rossmann_login",
            return_value=RossmannAccount("acct-9", "hsh-9"),
        ), patch(
            "workflows.rossmann_workflow._prepare_rossmann_session",
            return_value=(object(), Mock()),
        ), patch(
            "workflows.rossmann_workflow.collect_rossmann_receipts",
            return_value=[],
        ), patch(
            "workflows.rossmann_workflow.create_receipt_store",
            return_value=store,
        ), patch(
            "workflows.rossmann_workflow.import_local_sources",
            return_value=self._workflow_result(),
        ), patch("sys.stdout", new=stdout):
            success = run_rossmann_initial(prompt_login=True, output_dir=tmp_dir)
        self.assertTrue(success)

    def test_rossmann_initial_requires_auth(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.rossmann_workflow.create_receipt_store", return_value=Mock(),
        ), patch("sys.stdout", new=stdout):
            success = run_rossmann_initial(output_dir=tmp_dir)
        self.assertFalse(success)
        self.assertIn("Rossmann benötigt --cookies-file", stdout.getvalue())


class RunRossmannUpdateTests(unittest.TestCase):
    def test_run_rossmann_update_imports_existing_jsons(self):
        store = Mock()
        with tempfile.TemporaryDirectory() as tmp_dir:
            receipts_dir = Path(tmp_dir) / "receipts"
            receipts_dir.mkdir(parents=True)
            (receipts_dir / "abc.json").write_text('{"id":"abc"}', encoding="utf-8")

            with patch(
                "workflows.rossmann_workflow.create_receipt_store", return_value=store,
            ), patch(
                "workflows.rossmann_workflow.import_local_sources",
                return_value=WorkflowResult(
                    success=True,
                    summary=WorkflowSummary(
                        retailer="rossmann",
                        processed_count=1,
                        skipped_count=0,
                        total_receipts=1,
                        receipts_file="shopping_receipts.sqlite",
                        total_items=0,
                    ),
                    skipped_issues=[],
                    skipped_report_path=None,
                ),
            ) as import_pipeline:
                store.persist_receipts.return_value = PersistResult(1, 0, 1)
                success = run_rossmann_update(output_dir=tmp_dir)

        self.assertTrue(success)
        import_pipeline.assert_called_once()
        self.assertEqual(import_pipeline.call_args.kwargs["retailer"], "rossmann")

    def test_rossmann_update_fails_without_jsons(self):
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir, patch(
            "workflows.rossmann_workflow.create_receipt_store", return_value=Mock(),
        ), patch("sys.stdout", new=stdout):
            success = run_rossmann_update(output_dir=tmp_dir)
        self.assertFalse(success)
        self.assertIn("Keine Rossmann-Beleg-JSONs", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
