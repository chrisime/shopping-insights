"""Canonical dashboard error codes and payload helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


MISSING_DATABASE_ERROR_CODE: Final[int] = 101
NO_RECEIPTS_ERROR_CODE: Final[int] = 102

MISSING_DATABASE_ERROR_DETAIL: Final[str] = "missing_database"
NO_RECEIPTS_ERROR_DETAIL: Final[str] = "no_receipts"


@dataclass(frozen=True)
class DashboardError:
    error_code: int
    detail: str


def missing_database_error() -> DashboardError:
    return DashboardError(error_code=MISSING_DATABASE_ERROR_CODE, detail=MISSING_DATABASE_ERROR_DETAIL)


def no_receipts_error() -> DashboardError:
    return DashboardError(error_code=NO_RECEIPTS_ERROR_CODE, detail=NO_RECEIPTS_ERROR_DETAIL)
