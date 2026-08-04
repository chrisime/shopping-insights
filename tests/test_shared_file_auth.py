import unittest
import tempfile
from pathlib import Path

from auth.shared_file_auth import (
    parse_json_cookie_export,
    read_utf8_text_file,
)


class SharedFileAuthTests(unittest.TestCase):
    # --- parse_json_cookie_export ---
    def test_parse_json_cookie_export_top_level_cookies_key(self):
        raw = '{"cookies": [{"name": "test", "value": "1"}]}'
        result = parse_json_cookie_export(raw)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test")

    def test_parse_json_cookie_export_top_level_list(self):
        raw = '[{"name": "a", "value": "1"}, {"name": "b", "value": "2"}]'
        result = parse_json_cookie_export(raw)
        self.assertEqual(len(result), 2)

    def test_parse_json_cookie_export_filters_non_dict_entries(self):
        raw = '[{"name": "a"}, "not a dict", 42]'
        result = parse_json_cookie_export(raw)
        self.assertEqual(len(result), 1)

    def test_parse_json_cookie_export_returns_empty_list_for_unexpected_shape(self):
        raw = '"just a string"'
        result = parse_json_cookie_export(raw)
        self.assertEqual(result, [])

    def test_parse_json_cookie_export_returns_none_for_invalid_json(self):
        result = parse_json_cookie_export("not json at all")
        self.assertIsNone(result)

    def test_parse_json_cookie_export_empty_object_without_cookies(self):
        raw = '{"some": "data"}'
        result = parse_json_cookie_export(raw)
        self.assertEqual(result, [])

    # --- read_utf8_text_file ---
    def test_read_utf8_text_file_reads_content(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as f:
            f.write("Hello World")
            path = f.name
        try:
            content = read_utf8_text_file(path)
            self.assertEqual(content, "Hello World")
        finally:
            Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
