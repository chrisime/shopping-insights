"""Extract POS (point-of-sale) metadata from Lidl HTML receipts."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from .lidl_html_utils import extract_text_from_repeated_id

_LIDL_POS_LINE_RE = re.compile(
    r"(?P<market>\d{4})\s+(?P<cashier>\d{5,6})/(?P<register>\d{2,3})\s+"
    r"(?P<date>\d{2}\.\d{2}\.\d{2})\s+(?P<time>\d{2}:\d{2})"
)
_LIDL_SERIAL_LINE_RE = re.compile(r"LDL-\d{3}-(?P<market>\d{4})-(?P<register>\d{2,3})")

_LIDL_RECEIPT_ID_RE = re.compile(
    r"^2300"
    r"(?P<market>\d{4})"
    r"(?P<register>\d{1,3}?)"
    r"(?P<date>20\d{6})"
    r"(?P<cashier>\d+)$"
)


def infer_lidl_pos_metadata_from_receipt_id(receipt_id: str = "") -> Optional[dict]:
    """Infer market/register/cashier from the Lidl receipt id structure.

    The Lidl receipt id follows the pattern:
        2300 <market:4> <register:2-3> <YYYYMMDD:8> <cashier:5-6>
    """
    match = _LIDL_RECEIPT_ID_RE.match(receipt_id)
    if not match:
        return None

    market = match.group("market")
    register = match.group("register")
    cashier = match.group("cashier")

    if not cashier:
        return None

    return {
        "market": market,
        "register": register.zfill(2),
        "cashier": cashier.zfill(6),
        "bon_number": cashier.zfill(6),
    }


def apply_lidl_pos_metadata(
    receipt_data: Dict[str, Any],
    soup: BeautifulSoup,
    receipt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply market/register/cashier metadata from Lidl HTML with a receipt-id fallback."""
    pos_line = extract_text_from_repeated_id(soup, "return_code_line_13")
    serial_line = extract_text_from_repeated_id(soup, "return_code_line_3")

    metadata: Dict[str, Optional[str]] = {
        "market": None,
        "register": None,
        "cashier": None,
        "bon_number": None,
    }

    pos_match = _LIDL_POS_LINE_RE.search(pos_line)
    if pos_match:
        metadata["market"] = pos_match.group("market")
        metadata["register"] = pos_match.group("register")
        metadata["cashier"] = pos_match.group("cashier")
        metadata["bon_number"] = pos_match.group("cashier").zfill(6)
        metadata["date"] = pos_match.group("date")
        receipt_data.update(metadata)
        return receipt_data

    serial_match = _LIDL_SERIAL_LINE_RE.search(serial_line)
    if serial_match:
        metadata["market"] = serial_match.group("market")
        metadata["register"] = serial_match.group("register")

    inferred_metadata = infer_lidl_pos_metadata_from_receipt_id(receipt_id or "")
    if inferred_metadata:
        for field, value in inferred_metadata.items():
            if not metadata.get(field):
                metadata[field] = value

    receipt_data.update(metadata)
    return receipt_data
