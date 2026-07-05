"""Extract discount values from Lidl HTML receipts."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from shared.float_parser import parse_german_float
from bs4 import BeautifulSoup


def apply_lidl_discount_fields(receipt_data: Dict[str, Any], soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract and classify regular and sticker-like discounts from the purchase list text."""
    try:
        purchase_list = soup.find("span", class_="purchase_list")
        if not purchase_list:
            return receipt_data

        total_regular_savings = 0.0
        total_sticker_savings = 0.0
        sticker_percentages: list[int] = []

        for line in purchase_list.get_text().split("\n"):
            parsed_line = _parse_lidl_discount_line(line.strip())
            if not parsed_line:
                continue

            if parsed_line["kind"] == "preisvorteil":
                total_regular_savings += parsed_line["amount"]
                continue

            if parsed_line["kind"] == "sticker":
                sticker_percentages.append(parsed_line["percent"])
                total_sticker_savings += parsed_line["amount"]

        if total_regular_savings > 0:
            receipt_data["discount"] = round(total_regular_savings, 2)
        if sticker_percentages:
            receipt_data["sticker_discount_pct"] = sticker_percentages
        if total_sticker_savings > 0:
            receipt_data["sticker_discount"] = round(total_sticker_savings, 2)
    except (AttributeError, TypeError):
        pass

    return receipt_data


def _parse_lidl_discount_line(line: str) -> Optional[Dict[str, Any]]:
    """Classify a Lidl discount line into a known discount kind with parsed values."""
    if not line:
        return None

    line_lower = line.lower()
    amount_match = re.search(r"-?\s*(\d+[.,]\d{2})", line)
    amount = parse_german_float(amount_match.group(1)) if amount_match else None

    if "preisvorteil" in line_lower and "gesamter" not in line_lower and amount is not None:
        return {"kind": "preisvorteil", "amount": amount}

    if "lidl plus rabatt" in line_lower:
        return None

    pct_match = re.search(r"rabatt\s*(\d{1,3})\s*%", line_lower)
    if pct_match and amount is not None:
        try:
            return {"kind": "sticker", "amount": amount, "percent": int(pct_match.group(1))}
        except ValueError:
            return None

    if "rabatt" in line_lower and "gesamter" not in line_lower and amount is not None:
        return {"kind": "preisvorteil", "amount": amount}

    return None


def apply_lidl_plus_discount(receipt_data: Dict[str, Any], soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract the Lidl Plus discount (EUR gespart) from the receipt HTML."""
    try:
        vat_info_elements = soup.find_all("span", class_="vat_info")
        for element in vat_info_elements:
            element_text = element.get_text().strip()
            if "EUR gespart" in element_text:
                amount_match = re.search(r"(\d+,\d+)\s+EUR gespart", element_text)
                if amount_match:
                    receipt_data["lidlplus_discount"] = parse_german_float(
                        amount_match.group(1)
                    )
                    return receipt_data
    except (AttributeError, TypeError):
        pass

    try:
        page_text = soup.get_text()
        gespart_match = re.search(r"(\d+,\d+)\s+EUR gespart", page_text)
        if gespart_match:
            receipt_data["lidlplus_discount"] = parse_german_float(
                gespart_match.group(1)
            )
            return receipt_data
    except (AttributeError, TypeError):
        pass

    if receipt_data.get("lidlplus_discount") is None:
        receipt_data["lidlplus_discount"] = None

    return receipt_data
