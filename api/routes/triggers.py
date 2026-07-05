"""Fetch trigger API routes."""

from fastapi import APIRouter

from api.schemas.common import ItemResponse
from api.services.trigger_service import trigger_lidl_fetch, trigger_rewe_fetch


router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.post("/fetch/lidl", response_model=ItemResponse)
def trigger_lidl(days_back: int = 30) -> dict:
    return trigger_lidl_fetch(days_back=days_back)


@router.post("/fetch/rewe", response_model=ItemResponse)
def trigger_rewe(days_back: int = 30) -> dict:
    return trigger_rewe_fetch(days_back=days_back)
