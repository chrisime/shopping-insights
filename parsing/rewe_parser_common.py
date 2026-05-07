"""Shared helper utilities for REWE parser modules."""

from __future__ import annotations

from typing import Any


def to_rewe_float(value: Any) -> float:
    """Parse REWE decimal text or already numeric values into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(".", "").replace(",", "."))

