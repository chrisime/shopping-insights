"""Helpers for extracting normalized address objects from receipt header lines."""

from __future__ import annotations

import re
from typing import Iterable, Optional

from shared.addresses import normalize_address
from shared.metadata_markers import COMPANY_SUFFIXES, METADATA_MARKERS, STREET_SUFFIXES


HOUSE_NUMBER_PATTERN = r"\d+(?:\s*[A-Za-zÄÖÜäöüß])?(?:\s*[-/]\s*\d+(?:\s*[A-Za-zÄÖÜäöüß])?)*"

ADDRESS_ONE_LINE_RE = re.compile(
    r"^(?P<street>.+?)\s*"
    rf"(?P<street_no>{HOUSE_NUMBER_PATTERN})"
    r"(?:\s*,\s*|\s+)"
    r"(?P<zip>\d{5})\s+(?P<city>.+)$"
)
STREET_LINE_RE = re.compile(
    rf"^(?P<street>.+?)\s*(?P<street_no>{HOUSE_NUMBER_PATTERN})$"
)
HOUSE_NUMBER_ONLY_RE = re.compile(rf"^(?P<street_no>{HOUSE_NUMBER_PATTERN})$")
ZIP_CITY_RE = re.compile(r"^(?:D-)?(?P<zip>\d{5})\s+(?P<city>.+)$")
LETTER_RE = re.compile(r"[A-Za-zÄÖÜäöüß]")

COMPANY_SUFFIX_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in COMPANY_SUFFIXES) + r")\b",
    re.IGNORECASE,
)
STREET_SUFFIX_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(s) for s in STREET_SUFFIXES) + r")\b",
    re.IGNORECASE,
)
URL_OR_EMAIL_RE = re.compile(r"www\.|http|@")

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

    for index, line in enumerate(normalized_lines[:-2]):
        parsed = _parse_three_line_address(
            line,
            normalized_lines[index + 1],
            normalized_lines[index + 2],
        )
        if parsed:
            return parsed

    return None


def _parse_one_line_address(line: str) -> Optional[dict]:
    match = ADDRESS_ONE_LINE_RE.fullmatch(line)
    if not match:
        return None
    payload = match.groupdict()
    payload["street_no"] = re.sub(r"\s+", "", payload["street_no"])
    return normalize_address(payload)


def _parse_two_line_address(street_line: str, zip_city_line: str) -> Optional[dict]:
    street_match = STREET_LINE_RE.fullmatch(street_line)
    zip_city_match = ZIP_CITY_RE.fullmatch(zip_city_line)
    if not street_match or not zip_city_match:
        return None

    normalized_street = _normalize_line(street_match.group("street"))
    if not _is_street_line(normalized_street):
        return None

    payload = {
        "street": normalized_street,
        "street_no": re.sub(r"\s+", "", street_match.group("street_no")),
        "zip": zip_city_match.group("zip"),
        "city": zip_city_match.group("city"),
    }
    return normalize_address(payload)


def _parse_three_line_address(street_line: str, house_number_line: str, zip_city_line: str) -> Optional[dict]:
    house_number_match = HOUSE_NUMBER_ONLY_RE.fullmatch(house_number_line)
    zip_city_match = ZIP_CITY_RE.fullmatch(zip_city_line)
    if not house_number_match or not zip_city_match:
        return None
    if _parse_one_line_address(street_line) or _parse_two_line_address(street_line, house_number_line):
        return None

    normalized_street = _normalize_line(street_line)
    if not _is_street_line(normalized_street):
        return None

    payload = {
        "street": normalized_street,
        "street_no": re.sub(r"\s+", "", house_number_match.group("street_no")),
        "zip": zip_city_match.group("zip"),
        "city": zip_city_match.group("city"),
    }
    return normalize_address(payload)


def _is_street_line(line: str) -> bool:
    normalized = _normalize_line(line).lower()
    if not normalized:
        return False
    if LETTER_RE.search(normalized) is None:
        return False
    if COMPANY_SUFFIX_RE.search(normalized):
        return False
    if _is_metadata_line(normalized):
        return False
    if URL_OR_EMAIL_RE.search(normalized):
        return False
    return True


def _is_metadata_line(normalized: str) -> bool:
    return any(marker in normalized for marker in METADATA_MARKERS)


def _normalize_line(line: str) -> str:
    normalized = re.sub(r"\s+", " ", line or "").strip().strip(",")
    normalized = re.sub(r"^[*#=_\-\s]+|[*#=_\-\s]+$", "", normalized).strip()
    return normalized
