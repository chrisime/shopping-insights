"""Helpers for extracting normalized address objects from receipt header lines."""

from __future__ import annotations

import re
from typing import Iterable, Optional

from shared.addresses import normalize_address


ADDRESS_FIELDS = ("street", "street_no", "zip", "city")

ADDRESS_ONE_LINE_RE = re.compile(
    r"^(?P<street>.+?)\s+(?P<street_no>\d+[A-Za-z]?(?:[-/]\d+[A-Za-z]?)?)\s*,\s*(?P<zip>\d{5})\s+(?P<city>.+)$"
)
STREET_LINE_RE = re.compile(
    r"^(?P<street>.+?)\s+(?P<street_no>\d+[A-Za-z]?(?:[-/]\d+[A-Za-z]?)?)$"
)
ZIP_CITY_RE = re.compile(r"^(?P<zip>\d{5})\s+(?P<city>.+)$")

def extract_address_from_lines(lines: Iterable[str]) -> Optional[dict]:
    """Extract a normalized address from single-line or two-line header patterns."""
    normalized_lines = [_normalize_line(line) for line in lines]
    normalized_lines = [line for line in normalized_lines if line]

    for line in normalized_lines:
        parsed = _parse_one_line_address(line)
        if parsed:
            return parsed

    for index, line in enumerate(normalized_lines[:-1]):
        parsed = _parse_two_line_address(line, normalized_lines[index + 1])
        if parsed:
            return parsed

    return None


def _parse_one_line_address(line: str) -> Optional[dict]:
    match = ADDRESS_ONE_LINE_RE.fullmatch(line)
    if not match:
        return None
    return normalize_address(match.groupdict())


def _parse_two_line_address(street_line: str, zip_city_line: str) -> Optional[dict]:
    street_match = STREET_LINE_RE.fullmatch(street_line)
    zip_city_match = ZIP_CITY_RE.fullmatch(zip_city_line)
    if not street_match or not zip_city_match:
        return None
    payload = {
        "street": street_match.group("street"),
        "street_no": street_match.group("street_no"),
        "zip": zip_city_match.group("zip"),
        "city": zip_city_match.group("city"),
    }
    return normalize_address(payload)


def _normalize_line(line: object) -> str:
    return re.sub(r"\s+", " ", str(line or "")).strip().strip(",")



