"""KPI API routes."""



from fastapi import APIRouter

from api.schemas.kpis import (
    KpiBonusResponse,
    KpiSummaryResponse,
    KpiTopItemsResponse,
    KpiTrendResponse,
    KpiWeekdayResponse,
)
from api.services.kpi_service import get_bonus, get_summary, get_top_items, get_trend, get_weekday


router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/summary", response_model=KpiSummaryResponse)
def read_summary(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> KpiSummaryResponse:
    return KpiSummaryResponse(
        data=get_summary(
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
        )
    )


@router.get("/bonus", response_model=KpiBonusResponse)
def read_bonus(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> KpiBonusResponse:
    return KpiBonusResponse(data=get_bonus(retailer=retailer, start_date=start_date, end_date=end_date))


@router.get("/trend", response_model=KpiTrendResponse)
def read_trend(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    granularity: str = "day",
) -> KpiTrendResponse:
    return KpiTrendResponse(
        data=get_trend(
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
    )


@router.get("/top-items", response_model=KpiTopItemsResponse)
def read_top_items(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort: str = "quantity",
    limit: int = 20,
) -> KpiTopItemsResponse:
    return KpiTopItemsResponse(
        data=get_top_items(
            retailer=retailer,
            start_date=start_date,
            end_date=end_date,
            sort=sort,
            limit=limit,
        )
    )


@router.get("/weekday", response_model=KpiWeekdayResponse)
def read_weekday(
    retailer: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> KpiWeekdayResponse:
    return KpiWeekdayResponse(
        data=get_weekday(retailer=retailer, start_date=start_date, end_date=end_date)
    )
