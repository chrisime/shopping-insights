"""Receipt API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from api.schemas.common import ItemResponse, ListResponse
from api.services.receipt_service import get_receipt, get_receipt_items, get_receipt_payments, list_receipts, list_receipts_by_date_range, list_receipts_by_item


router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get("", response_model=ListResponse)
def read_receipts(
    retailer: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    return list_receipts(retailer=retailer, page=page, page_size=page_size)


@router.get("/by-item")
def read_receipts_by_item(
    name: str,
    retailer: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    return list_receipts_by_item(
        name=name,
        retailer=retailer,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/by-date")
def read_receipts_by_date(
    start_date: str,
    end_date: str,
    retailer: Optional[str] = None,
) -> list[dict]:
    return list_receipts_by_date_range(
        start_date=start_date,
        end_date=end_date,
        retailer=retailer,
    )


@router.get("/{receipt_id}", response_model=ItemResponse)
def read_receipt(receipt_id: str, retailer: Optional[str] = None) -> dict:
    try:
        return get_receipt(receipt_id, retailer=retailer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Receipt not found") from exc


@router.get("/{receipt_id}/items", response_model=ItemResponse)
def read_receipt_items(receipt_id: str, retailer: Optional[str] = None) -> dict:
    try:
        return get_receipt_items(receipt_id, retailer=retailer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Receipt not found") from exc


@router.get("/{receipt_id}/payments", response_model=ItemResponse)
def read_receipt_payments(receipt_id: str, retailer: Optional[str] = None) -> dict:
    try:
        return get_receipt_payments(receipt_id, retailer=retailer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Receipt not found") from exc
