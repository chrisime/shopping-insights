import unittest

from workflows.error_mapping import (
    build_exception_issue,
    build_exception_skip_result,
    build_validation_issue,
    build_validation_skip_result,
)


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
    def test_build_exception_issue_uses_custom_reason_formatter(self):
        issue = build_exception_issue(
            source_id="receipt-1",
            exc=ValueError("kaputt"),
            detail_key="file",
            reason_formatter=lambda exc: f"Boom: {exc}",
        )

        self.assertEqual(issue.source_id, "receipt-1")
        self.assertEqual(issue.reason, "Boom: kaputt")
        self.assertEqual(issue.detail_key, "file")

    def test_build_validation_issue_renders_validator_prefix_and_details(self):
        exc = _FakeValidationError([_FakeValidationIssue("items: fehlen"), _FakeValidationIssue("total: ungültig")])

        issue = build_validation_issue("receipt-1", exc)

        self.assertEqual(
            issue.reason,
            "Validatorfehler: items: fehlen; total: ungültig",
        )

    def test_build_validation_skip_result_uses_same_validation_rendering(self):
        exc = _FakeValidationError([_FakeValidationIssue("items: fehlen")])

        parse_result = build_validation_skip_result(exc)

        self.assertIsNone(parse_result.receipt_data)
        self.assertEqual(parse_result.skip_reason, "Validatorfehler: items: fehlen")

    def test_build_exception_skip_result_defaults_to_exception_text(self):
        parse_result = build_exception_skip_result(ValueError("kaputt"))

        self.assertIsNone(parse_result.receipt_data)
        self.assertEqual(parse_result.skip_reason, "kaputt")


if __name__ == "__main__":
    unittest.main()

