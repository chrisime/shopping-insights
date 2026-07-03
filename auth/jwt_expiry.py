"""Generic helpers for extracting JWT expiry from a cookie jar."""

from __future__ import annotations

import base64
import simplejson
import time
from typing import Optional


def extract_jwt_expiry_epoch(cookie_jar, cookie_name: str) -> Optional[int]:
    """Return the exp claim (unix epoch) of a JWT cookie when available and parseable."""
    token = cookie_jar.get(cookie_name)
    if not token or "." not in token:
        return None

    parts = token.split(".")
    if len(parts) < 2:
        return None

    payload_part = parts[1]
    padding = "=" * (-len(payload_part) % 4)
    try:
        payload_raw = base64.urlsafe_b64decode(payload_part + padding)
        payload = simplejson.loads(payload_raw.decode("utf-8"))
    except Exception:
        return None

    exp = payload.get("exp") if isinstance(payload, dict) else None
    if isinstance(exp, int):
        return exp
    if isinstance(exp, float):
        return int(exp)
    return None


def is_jwt_expired(expiry_epoch: int, leeway_seconds: int = 60) -> bool:
    """Return True when a JWT is expired or about to expire soon."""
    return expiry_epoch <= int(time.time()) + leeway_seconds

