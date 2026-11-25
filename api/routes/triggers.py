"""Fetch trigger API routes."""

from fastapi import APIRouter, HTTPException, Query

from api.errors import ApiErrorCode
from api.schemas.common import ItemResponse
from api.schemas.imports import RossmannLogin
from api.services.trigger_service import trigger_dm_fetch, trigger_lidl_fetch, trigger_rewe_fetch, trigger_rossmann_fetch

from auth.rossmann_auth import RossmannAuthError
from workflows.workflow_errors import rossmann_initial_error


router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.post("/fetch/lidl", response_model=ItemResponse)
def trigger_lidl(days_back: int = Query(30, ge=0)) -> dict:
    return trigger_lidl_fetch(days_back=days_back)


@router.post("/fetch/rewe", response_model=ItemResponse)
def trigger_rewe(days_back: int = Query(30, ge=0)) -> dict:
    return trigger_rewe_fetch(days_back=days_back)


@router.post("/fetch/dm", response_model=ItemResponse)
def trigger_dm(days_back: int = Query(30, ge=0)) -> dict:
    return trigger_dm_fetch(days_back=days_back)


@router.post("/fetch/rossmann", response_model=ItemResponse)
def trigger_rossmann(login: RossmannLogin, days_back: int = Query(30, ge=0)) -> dict:
    email = login.email.strip()
    if not email or not login.password.get_secret_value():
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": int(ApiErrorCode.INVALID_REQUEST),
                "detail": "Rossmann login requires an email and password",
            },
        )

    try:
        return trigger_rossmann_fetch(email=email, password=login.password, days_back=days_back)
    except RossmannAuthError:
        info = rossmann_initial_error(2407)
        raise HTTPException(
            status_code=401,
            detail={"error_code": info.error_code, "detail": info.detail},
        ) from None
