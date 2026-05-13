import unittest

from result_types import ReceiptParseResult
from workflows.error_mapping import render_exception_reason, render_validation_reason


class _FakeValidationIssue:
    def __init__(self, text: str):
        self._text = text

    def render(self) -> str:
        return self._text


class _FakeValidationError(Exception):
    def __init__(self, issues):
        super().__init__("validator kaputt")
        self.issues = issues

class WorkflowErrorMappingTests(unittest.TestCase):
    def test_render_exception_reason_uses_rewe_pdf_parse_reason_kind(self):
        reason = render_exception_reason(ValueError("kaputt"), reason_kind="rewe_pdf_parse")

        self.assertEqual(reason, "PDF konnte nicht gelesen werden: kaputt")

    def test_render_validation_reason_renders_validator_prefix_and_details(self):
        exc = _FakeValidationError([_FakeValidationIssue("items: fehlen"), _FakeValidationIssue("total: ungültig")])

        reason = render_validation_reason(exc)

        self.assertEqual(
            reason,
            "Validatorfehler: items: fehlen; total: ungültig",
        )

    def test_receipt_parse_result_can_use_render_validation_reason(self):
        exc = _FakeValidationError([_FakeValidationIssue("items: fehlen")])

        parse_result = ReceiptParseResult(receipt_data=None, skip_reason=render_validation_reason(exc))

        self.assertIsNone(parse_result.receipt_data)
        self.assertEqual(parse_result.skip_reason, "Validatorfehler: items: fehlen")

    def test_receipt_parse_result_can_use_render_exception_reason(self):
        parse_result = ReceiptParseResult(receipt_data=None, skip_reason=render_exception_reason(ValueError("kaputt")))

        self.assertIsNone(parse_result.receipt_data)
        self.assertEqual(parse_result.skip_reason, "kaputt")


if __name__ == "__main__":
    unittest.main()

