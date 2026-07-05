import unittest
import tempfile
from pathlib import Path

from auth.shared_file_auth import (
    CookieNameAnalysis,
    CookieDiagnosticProfile,
    CookieDiagnosticExtras,
    assess_cookie_quality,
    parse_json_cookie_export,
    read_utf8_text_file,
)


class SharedFileAuthTests(unittest.TestCase):
    # --- CookieNameAnalysis ---
    def test_cookie_name_analysis_creation(self):
        analysis = CookieNameAnalysis(
            cookie_names=frozenset({"a", "b"}),
            missing_required=("c",),
            present_recommended=("b",),
            missing_recommended=("d",),
        )
        self.assertEqual(analysis.cookie_names, frozenset({"a", "b"}))
        self.assertEqual(analysis.missing_required, ("c",))
        self.assertEqual(analysis.present_recommended, ("b",))

    # --- CookieDiagnosticProfile ---
    def test_cookie_diagnostic_profile_defaults(self):
        profile = CookieDiagnosticProfile(
            store_name="Test",
            required_cookies={"x"},
            recommended_cookies={"y"},
        )
        self.assertEqual(profile.store_name, "Test")
        self.assertEqual(profile.rot_summary, "wahrscheinlich nicht ausreichend")
        self.assertEqual(profile.gruen_summary, "Datei wirkt direkt nutzbar")

    # --- CookieDiagnosticExtras ---
    def test_cookie_diagnostic_extras_defaults(self):
        extras = CookieDiagnosticExtras()
        self.assertEqual(extras.lines, [])
        self.assertEqual(extras.steps, [])

    def test_cookie_diagnostic_extras_with_values(self):
        extras = CookieDiagnosticExtras(lines=["Line 1"], steps=["Step 1"])
        self.assertEqual(extras.lines, ["Line 1"])
        self.assertEqual(extras.steps, ["Step 1"])

    # --- assess_cookie_quality ---
    def test_assess_cookie_quality_returns_rot_when_required_missing(self):
        profile = CookieDiagnosticProfile(
            store_name="Lidl",
            required_cookies={"authToken"},
            recommended_cookies={"rememberMe"},
            rot_summary="rot summary",
            rot_recommendation="do this",
        )
        status, summary, recommendation = assess_cookie_quality(
            {"some_other"}, profile
        )
        self.assertEqual(status, "ROT")
        self.assertEqual(summary, "rot summary")
        self.assertEqual(recommendation, "do this")

    def test_assess_cookie_quality_returns_gruen_when_all_present(self):
        profile = CookieDiagnosticProfile(
            store_name="Lidl",
            required_cookies={"authToken"},
            recommended_cookies={"rememberMe"},
            gruen_summary="alles gut",
            gruen_recommendation="weiter so",
        )
        status, summary, recommendation = assess_cookie_quality(
            {"authToken", "rememberMe"}, profile
        )
        self.assertEqual(status, "GRUEN")
        self.assertEqual(summary, "alles gut")

    def test_assess_cookie_quality_returns_gelb_when_required_ok_but_recommended_missing(self):
        profile = CookieDiagnosticProfile(
            store_name="Lidl",
            required_cookies={"authToken"},
            recommended_cookies={"rememberMe"},
            gelb_summary="geht so",
            gelb_recommendation="vielleicht nachbessern",
        )
        status, summary, recommendation = assess_cookie_quality(
            {"authToken"}, profile
        )
        self.assertEqual(status, "GELB")
        self.assertEqual(summary, "geht so")

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
