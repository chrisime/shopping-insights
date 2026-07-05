"""Item API routes."""

from typing import Optional

from fastapi import APIRouter

from api.schemas.common import ListResponse
from api.services.item_service import list_items


router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ListResponse)
def read_items(
    retailer: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    return list_items(retailer=retailer, search=search, page=page, page_size=page_size)
