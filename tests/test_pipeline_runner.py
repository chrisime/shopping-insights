import unittest
from unittest.mock import Mock, patch

from result_types import WorkflowSummary
from workflows.pipeline_runner import parse_receipts, validate_receipts
from workflows.pipeline_types import ParsedReceiptRecord, RawReceiptRecord, ReceiptIssue, WorkflowResult


class PipelineRunnerTests(unittest.TestCase):
    def test_parse_receipts_uses_lidl_parser_for_lidl_records(self):
        raw_records = [RawReceiptRecord(source_id="receipt-1", payload={"ticket": True})]

        with patch(
            "workflows.pipeline_runner.parse_raw_record_for_retailer",
            return_value={"id": "receipt-1", "items": []},
        ) as parse_raw_record_for_retailer:
            result = parse_receipts(raw_records, retailer="lidl")

        parse_raw_record_for_retailer.assert_called_once_with(raw_records[0], "lidl")
        self.assertEqual(len(result.records), 1)
        self.assertEqual(result.issues, [])

    def test_parse_receipts_updates_progress_items_count_from_parsed_receipts(self):
        raw_records = [RawReceiptRecord(source_id="receipt-1.pdf", payload="receipt-1.pdf")]

        progress_display_cls = Mock()
        with (
            patch("workflows.pipeline_runner.ReceiptProgressDisplay", progress_display_cls),
            patch(
                "workflows.pipeline_runner.parse_raw_record_for_retailer",
                return_value={"id": "receipt-1", "items": [{"name": "A"}, {"name": "B"}]},
            ),
        ):
            result = parse_receipts(raw_records, retailer="rewe", detail_key="file")

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

        with patch("workflows.pipeline_runner.validate_receipt_for_retailer") as validate_receipt_for_retailer:
            result = validate_receipts(
                parsed_records,
                retailer="rewe",
                detail_key="file",
            )

        validate_receipt_for_retailer.assert_called_once_with({"id": "receipt-1", "items": []}, "rewe")
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

        with patch("workflows.pipeline_runner.validate_receipt_for_retailer"):
            result = validate_receipts(
                parsed_records,
                retailer="rewe",
                detail_key="file",
            )

        self.assertEqual(result.total_items, 2)


    def test_receipt_issue_renders_detail_dict(self):
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
            [issue.as_detail() for issue in result.skipped_issues],
            [{"receipt_id": "receipt-1", "reason": "kaputt"}],
        )


if __name__ == "__main__":
    unittest.main()

