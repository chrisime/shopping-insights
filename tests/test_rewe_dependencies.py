from importlib.util import find_spec
import unittest

from reporting.rewe_api_reporting import print_rewe_http_error
from reporting.rewe_workflow_reporting import write_rewe_skipped_receipts_report


class ReweArchitectureTests(unittest.TestCase):
	def test_rewe_reporting_symbols_come_from_reporting_package(self):
		self.assertEqual(print_rewe_http_error.__module__, "reporting.rewe_api_reporting")
		self.assertEqual(
			write_rewe_skipped_receipts_report.__module__,
			"reporting.rewe_workflow_reporting",
		)

	def test_rewe_reporting_modules_no_longer_exist_under_diagnostics(self):
		self.assertIsNone(find_spec("diagnostics.rewe_api_reporting"))
		self.assertIsNone(find_spec("diagnostics.rewe_workflow_reporting"))


if __name__ == "__main__":
	unittest.main()

