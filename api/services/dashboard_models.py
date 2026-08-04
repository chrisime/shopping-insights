"""Dashboard DTOs — dataclasses that model the Vue dashboard payload."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from api.services.dashboard_errors import DashboardError
from shared.kpi_dtos import BasicKPIs, RetailerBonusKPIs, TimeSeriesRow, TopItemRow, WeekdayRow


@dataclass(frozen=True)
class DashboardDerivedMetrics:
    total_before_discount: float
    discount_pct: float
    bonus_redeemed_pct: float
    total_bonus_redeemed: float
    total_savings_no_deposit: float
    total_savings_pct: float
    lidlplus_pct: float
    sticker_pct: float


@dataclass(frozen=True)
class DashboardState:
    retailer: str | None
    start_date: str | None
    end_date: str | None
    time_granularity: str
    spending_view: str
    top_view: str
    top_limit: int
    search: str | None
    page: int
    available_kpis: BasicKPIs
    kpis: BasicKPIs
    bonus_kpis: RetailerBonusKPIs
    derived: DashboardDerivedMetrics
    time_series: list[TimeSeriesRow]
    weekday: list[WeekdayRow]
    top_items: list[TopItemRow]
    top_items_total: int
    min_date: str | None
    max_date: str | None
    error: DashboardError | None = None
    rewe_kpis: BasicKPIs | None = None
    lidl_kpis: BasicKPIs | None = None
    rewe_bonus_kpis: RetailerBonusKPIs | None = None
    lidl_bonus_kpis: RetailerBonusKPIs | None = None


@dataclass(frozen=True)
class DashboardSection:
    kind: str
    title: str
    items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "title": self.title, "items": [dict(item) for item in self.items]}


@dataclass(frozen=True)
class DashboardPageModel:
    title: str
    sections: list[DashboardSection]
    min_date: str | None = None
    max_date: str | None = None
    error: DashboardError | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "sections": [section.to_dict() for section in self.sections],
        }
        if self.min_date is not None or self.error is not None:
            payload["min_date"] = self.min_date
        if self.max_date is not None or self.error is not None:
            payload["max_date"] = self.max_date
        if self.error is not None:
            payload["error"] = {"error_code": self.error.error_code, "detail": self.error.detail}
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DashboardPageModel":
        error_payload = payload.get("error")
        error = DashboardError(**error_payload) if error_payload is not None else None
        return cls(
            title=payload["title"],
            sections=[DashboardSection(**section) for section in payload.get("sections", [])],
            min_date=payload.get("min_date"),
            max_date=payload.get("max_date"),
            error=error,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> "DashboardPageModel":
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class VueDashboardPayload:
    title: str
    sections: list[dict[str, Any]]
    min_date: str | None = None
    max_date: str | None = None
    error: DashboardError | None = None

    @classmethod
    def from_page_model(cls, page: DashboardPageModel) -> "VueDashboardPayload":
        return cls(
            title=page.title,
            sections=[section.to_dict() for section in page.sections],
            min_date=page.min_date,
            max_date=page.max_date,
            error=page.error,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": self.title,
            "sections": [dict(section) for section in self.sections],
        }
        if self.min_date is not None or self.error is not None:
            payload["min_date"] = self.min_date
        if self.max_date is not None or self.error is not None:
            payload["max_date"] = self.max_date
        if self.error is not None:
            payload["error"] = {"error_code": self.error.error_code, "detail": self.error.detail}
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VueDashboardPayload":
        error_payload = payload.get("error")
        error = DashboardError(**error_payload) if error_payload is not None else None
        return cls(
            title=payload["title"],
            sections=[dict(section) for section in payload.get("sections", [])],
            min_date=payload.get("min_date"),
            max_date=payload.get("max_date"),
            error=error,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> "VueDashboardPayload":
        return cls.from_dict(json.loads(payload))
