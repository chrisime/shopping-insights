import unittest
from unittest.mock import Mock, patch

from result_types import PersistResult, WorkflowSummary
from workflows.pipeline_runner import parse_receipts, persist_valid_receipts, validate_receipts
from workflows.pipeline_types import ParsedReceiptRecord, RawReceiptRecord, ReceiptIssue, WorkflowResult


class _FakeStore:
    def persist_receipts(self, receipts, retailer, file_path=None):
        return PersistResult(
            created_count=2,
            updated_count=1,
            total_receipts=5,
        )


class PipelineRunnerTests(unittest.TestCase):
    def test_parse_receipts_uses_lidl_parser_for_lidl_records(self):
        raw_records = [RawReceiptRecord(source_id="receipt-1", payload={"ticket": True})]
        parse_record = Mock(return_value={"id": "receipt-1", "items": []})

        result = parse_receipts(raw_records, parse_record=parse_record)

        parse_record.assert_called_once_with(raw_records[0])
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.issues, [])

    def test_parse_receipts_updates_progress_items_count_from_parsed_receipts(self):
        raw_records = [RawReceiptRecord(source_id="receipt-1.pdf", payload="receipt-1.pdf")]
        parse_record = Mock(return_value={"id": "receipt-1", "items": [{"name": "A"}, {"name": "B"}]})

        progress_display_cls = Mock()
        with patch("workflows.pipeline_runner.ReceiptProgressDisplay", progress_display_cls):
            result = parse_receipts(raw_records, parse_record=parse_record, detail_key="file")

        self.assertEqual(len(result.records), 1)
        final_state = progress_display_cls.return_value.render.call_args_list[-1].args[0]
        self.assertEqual(final_state.items, 2)

    def test_validate_receipts_uses_rewe_validator_for_rewe_records(self):
        parsed_records = [
            ParsedReceiptRecord(
                source_id="receipt-1.pdf",
                receipt_data={"id": "receipt-1", "items": []},
            )
        ]
        validate_receipt = Mock()

        result = validate_receipts(
            parsed_records,
            validate_receipt=validate_receipt,
            validation_error_types=(ValueError,),
            detail_key="file",
        )

        validate_receipt.assert_called_once_with({"id": "receipt-1", "items": []})
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.issues, [])
        self.assertEqual(result.total_items, 0)

    def test_validate_receipts_tracks_total_items_for_summary_reuse(self):
        parsed_records = [
            ParsedReceiptRecord(
                source_id="receipt-1.pdf",
                receipt_data={"id": "receipt-1", "items": [{"name": "A"}, {"name": "B"}]},
            )
        ]

        result = validate_receipts(
            parsed_records,
            validate_receipt=Mock(),
            validation_error_types=(ValueError,),
            detail_key="file",
        )

        self.assertEqual(result.total_items, 2)

    def test_persist_valid_receipts_returns_store_result(self):
        store = _FakeStore()

        result = persist_valid_receipts(
            [{"id": "1", "items": []}],
            retailer="lidl",
            store=store,
        )

        self.assertEqual(result.processed_count, 3)
        self.assertEqual(result.total_receipts, 5)

    def test_workflow_result_renders_skipped_details_from_issues(self):
        result = WorkflowResult(
            success=True,
            summary=WorkflowSummary(
                retailer="lidl",
                processed_count=1,
                skipped_count=1,
                total_receipts=5,
                receipts_file="lidl_receipts.json",
            ),
            skipped_issues=[ReceiptIssue("receipt-1", "kaputt")],
        )

        self.assertEqual(
            result.skipped_details(),
            [{"receipt_id": "receipt-1", "reason": "kaputt"}],
        )


if __name__ == "__main__":
    unittest.main()

