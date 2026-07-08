"""Reusable section-based dashboard page models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from api.services.dashboard_errors import DashboardError
from api.services.dashboard_state import DashboardState


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


def build_dashboard_page_model(state: DashboardState) -> DashboardPageModel:
    if _is_empty_state(state):
        return DashboardPageModel(
            title="Shopping Analyzer Dashboard",
            sections=[],
            min_date=_date_text(state.min_date),
            max_date=_date_text(state.max_date),
            error=state.error,
        )

    sections = [DashboardSection(kind="metrics", title="Kennzahlen", items=[_build_kpi_metrics(state)])]

    sections.extend(
        [
            DashboardSection(
                kind="time_series",
                title="Ausgaben über Zeit",
                items=[
                    {"period": row.period, "total_spent": row.total_spent, "receipt_count": row.receipt_count}
                    for row in state.time_series
                ],
            ),
            DashboardSection(
                kind="weekday",
                title="Einkaufsverhalten nach Wochentag",
                items=[
                    {
                        "weekday": row.weekday,
                        "weekday_name": row.weekday_name,
                        "trip_count": row.trip_count,
                        "avg_spent": row.avg_spent,
                        "total_spent": row.total_spent,
                    }
                    for row in state.weekday
                ],
            ),
            DashboardSection(
                kind="top_items",
                title="Top-Artikel",
                items=[
                    {
                        "name": row.name,
                        "total_quantity": row.total_quantity,
                        "total_spent": row.total_spent,
                        "purchase_count": row.purchase_count,
                        "unit": row.unit,
                    }
                    for row in state.top_items
                ],
            ),
        ]
    )

    # append pagination metadata to the top_items section
    if sections and sections[-1].kind == "top_items":
        last = sections[-1]
        sections[-1] = DashboardSection(
            kind="top_items",
            title=last.title,
            items=[
                {**item, "total_count": state.top_items_total, "page": state.page, "page_size": state.top_limit}
                for item in last.items
            ],
        )
    return DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=sections,
        min_date=_date_text(state.min_date),
        max_date=_date_text(state.max_date),
        error=state.error,
    )


def _build_kpi_metrics(state: DashboardState) -> dict[str, float]:
    metrics: dict[str, float] = {
        "spendings": state.kpis.total_spent,
        "spendings_without_discount": state.derived.total_before_discount,
        "receipt_count": float(state.kpis.total_receipts),
        "avg_receipt_amount": state.kpis.avg_receipt,
        "saved_deposit": state.kpis.total_saved_deposit,
        "total_savings": state.derived.total_savings_no_deposit,
        "total_savings_pct": state.derived.total_savings_pct,
    }

    if state.retailer in (None, "rewe"):
        rewe_bonus = (
            state.rewe_bonus_kpis
            if state.retailer is None and state.rewe_bonus_kpis is not None
            else state.bonus_kpis
        )
        rewe_regular = (
            state.rewe_kpis.total_discount
            if state.retailer is None and state.rewe_kpis is not None
            else state.kpis.total_discount
        )
        rewe_bonus_open = max(0.0, rewe_bonus.rewe_bonus_collected - rewe_bonus.rewe_bonus_redeemed)
        metrics["rewe_discount_amount"] = rewe_regular
        metrics["rewe_discount_pct"] = _pct(rewe_regular, _retailer_spent(state, "rewe"))
        metrics["rewe_bonus_collected"] = rewe_bonus.rewe_bonus_collected
        metrics["rewe_bonus_balance"] = rewe_bonus.rewe_bonus_balance
        metrics["rewe_bonus_redeemed"] = rewe_bonus.rewe_bonus_redeemed
        metrics["rewe_bonus_open"] = rewe_bonus_open

    if state.retailer in (None, "lidl"):
        lidl_bonus = (
            state.lidl_bonus_kpis
            if state.retailer is None and state.lidl_bonus_kpis is not None
            else state.bonus_kpis
        )
        lidl_regular = (
            state.lidl_kpis.total_discount
            if state.retailer is None and state.lidl_kpis is not None
            else state.kpis.total_discount
        )
        metrics["lidlplus_discount_amount"] = lidl_bonus.lidlplus_discount
        metrics["lidlplus_discount_pct"] = _pct(lidl_bonus.lidlplus_discount, _retailer_spent(state, "lidl"))
        metrics["sticker_discount_amount"] = lidl_bonus.sticker_discount
        metrics["sticker_discount_pct"] = _pct(lidl_bonus.sticker_discount, _retailer_spent(state, "lidl"))
        metrics["lidl_discount_amount"] = lidl_regular
        metrics["lidl_discount_pct"] = _pct(lidl_regular, _retailer_spent(state, "lidl"))

    return metrics


def _retailer_spent(state: DashboardState, retailer: str) -> float:
    if state.retailer == retailer:
        return state.kpis.total_spent
    if retailer == "rewe" and state.rewe_kpis is not None:
        return state.rewe_kpis.total_spent
    if retailer == "lidl" and state.lidl_kpis is not None:
        return state.lidl_kpis.total_spent
    return state.kpis.total_spent


def _pct(value: float, total: float) -> float:
    if not total:
        return 0.0
    return round((value / total) * 100, 2)


def _date_text(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _is_empty_state(state: DashboardState) -> bool:
    return state.error is not None
