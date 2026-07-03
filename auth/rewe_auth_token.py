"""Shared helpers for inspecting REWE rstp JWT expiry."""

from __future__ import annotations

import base64
import json
import time
from typing import Optional



def extract_rewe_rstp_expiry_epoch(cookie_jar) -> Optional[int]:
    """Return rstp exp claim (unix epoch) when available and parseable."""
    rstp_token = cookie_jar.get("rstp")
    if not rstp_token or "." not in rstp_token:
        return None

    parts = rstp_token.split(".")
    if len(parts) < 2:
        return None

    payload_part = parts[1]
    padding = "=" * (-len(payload_part) % 4)
    try:
        payload_raw = base64.urlsafe_b64decode(payload_part + padding)
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return None

    exp = payload.get("exp") if isinstance(payload, dict) else None
    if isinstance(exp, int):
        return exp
    if isinstance(exp, float):
        return int(exp)
    return None



def is_rewe_rstp_expired(expiry_epoch: int, leeway_seconds: int = 60) -> bool:
    """Return True when rstp is expired or about to expire soon."""
    return expiry_epoch <= int(time.time()) + leeway_seconds

