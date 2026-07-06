"""Schemas for import job API endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ImportStartRequest(BaseModel):
    retailer: Literal["lidl", "rewe"]


class ImportStartResponse(BaseModel):
    job_id: str
    retailer: Literal["lidl", "rewe"]
