"""Export API routes."""

from typing import Optional

from fastapi import APIRouter

from api.schemas.common import ItemResponse
from api.services import export_service


router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/receipts", response_model=ItemResponse)
def export_receipts_endpoint(
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    return export_service.export_receipts(retailer=retailer, start_date=start_date, end_date=end_date)


@router.get("/kpis", response_model=ItemResponse)
def export_kpis_endpoint(retailer: Optional[str] = None) -> dict:
    return {"data": export_service.export_kpis(retailer=retailer)}
