import unittest

from auth.cookie_diagnostics import (
    CookieNameAnalysis,
    CookieDiagnosticProfile,
    CookieDiagnosticExtras,
    assess_cookie_quality,
)


class CookieDiagnosticsTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
