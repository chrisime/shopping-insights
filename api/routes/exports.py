"""Export API routes."""



from fastapi import APIRouter

from api.schemas.common import ItemResponse
from api.services import export_service


router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/receipts", response_model=ItemResponse)
def export_receipts_endpoint(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    return export_service.export_receipts(retailer=retailer, start_date=start_date, end_date=end_date)


@router.get("/kpis", response_model=ItemResponse)
def export_kpis_endpoint(retailer: str | None = None) -> dict:
    return {"data": export_service.export_kpis(retailer=retailer)}
