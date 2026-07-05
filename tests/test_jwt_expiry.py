import base64
import unittest
from unittest.mock import patch

import simplejson

from auth.jwt_expiry import extract_jwt_expiry_epoch, is_jwt_expired


def _build_jwt(payload: dict) -> str:
    header = base64.urlsafe_b64encode(
        simplejson.dumps({"alg": "none"}, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    body = base64.urlsafe_b64encode(
        simplejson.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    return f"{header}.{body}.sig"


class JwtExpiryTests(unittest.TestCase):
    # --- extract_jwt_expiry_epoch ---
    def test_extract_jwt_expiry_epoch_extracts_exp_claim(self):
        token = _build_jwt({"exp": 1700000000})
        jar = {"session_token": token}
        result = extract_jwt_expiry_epoch(jar, "session_token")
        self.assertEqual(result, 1700000000)

    def test_extract_jwt_expiry_epoch_handles_float_exp(self):
        token = _build_jwt({"exp": 1700000000.5})
        jar = {"session_token": token}
        result = extract_jwt_expiry_epoch(jar, "session_token")
        self.assertEqual(result, 1700000000)

    def test_extract_jwt_expiry_epoch_returns_none_when_no_dot(self):
        jar = {"session_token": "not-a-jwt"}
        self.assertIsNone(extract_jwt_expiry_epoch(jar, "session_token"))

    def test_extract_jwt_expiry_epoch_returns_none_when_token_missing(self):
        self.assertIsNone(extract_jwt_expiry_epoch({}, "missing"))

    def test_extract_jwt_expiry_epoch_returns_none_when_payload_not_dict(self):
        token = _build_jwt(["just", "a", "list"])
        jar = {"session_token": token}
        self.assertIsNone(extract_jwt_expiry_epoch(jar, "session_token"))

    def test_extract_jwt_expiry_epoch_returns_none_when_no_exp(self):
        token = _build_jwt({"sub": "user123"})
        jar = {"session_token": token}
        self.assertIsNone(extract_jwt_expiry_epoch(jar, "session_token"))

    # --- is_jwt_expired ---
    @patch("time.time", return_value=1700000000.0)
    def test_is_jwt_expired_returns_true_when_expired(self, _):
        self.assertTrue(is_jwt_expired(1699999900))

    @patch("time.time", return_value=1700000000.0)
    def test_is_jwt_expired_returns_true_within_leeway(self, _):
        self.assertTrue(is_jwt_expired(1700000030, leeway_seconds=60))

    @patch("time.time", return_value=1700000000.0)
    def test_is_jwt_expired_returns_false_when_still_valid(self, _):
        self.assertFalse(is_jwt_expired(1700000100))

    @patch("time.time", return_value=1700000000.0)
    def test_is_jwt_expired_respects_custom_leeway(self, _):
        self.assertFalse(is_jwt_expired(1700000050, leeway_seconds=30))


if __name__ == "__main__":
    unittest.main()
