"""Shared API response schemas."""

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


class ItemResponse(BaseModel):
    data: Any
