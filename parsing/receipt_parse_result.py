"""Shared parse result type for receipt parsers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ReceiptParseResult:
    """Structured parser result with optional receipt data and skip reason."""

    receipt_data: Optional[Dict[str, Any]]
    skip_reason: Optional[str] = None

