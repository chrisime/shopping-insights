"""Shared API response schemas."""

from math import ceil
from typing import Any

from pydantic import BaseModel


class PaginationMeta(BaseModel):
    total: int
    page_total: int
    page: int
    page_size: int


class ListResponse(BaseModel):
    data: list[dict]
    meta: PaginationMeta


def paginate_rows(rows: list[dict[str, Any]], page: int, page_size: int) -> dict[str, Any]:
    total = len(rows)
    page_total = max(1, ceil(total / page_size)) if total else 0
    start = (page - 1) * page_size
    return {
        "data": rows[start:start + page_size],
        "meta": {
            "total": total,
            "page_total": page_total,
            "page": page,
            "page_size": page_size,
        },
    }


class ItemResponse(BaseModel):
    data: Any
