"""Item API routes."""

from fastapi import APIRouter, Query

from api.schemas.common import ListResponse
from api.services.item_service import list_items


router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ListResponse)
def read_items(
    retailer: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1),
) -> dict:
    return list_items(retailer=retailer, search=search, page=page, page_size=page_size)
