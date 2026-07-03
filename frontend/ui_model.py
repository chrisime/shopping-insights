"""Reusable section-based dashboard page models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from frontend.dashboard_state import DashboardState


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

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "sections": [section.to_dict() for section in self.sections]}


def build_dashboard_page_model(state: DashboardState) -> DashboardPageModel:
    sections = [
        DashboardSection(
            kind="metrics",
            title="Kennzahlen",
            items=_build_metric_items(state),
        ),
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
    return DashboardPageModel(title="Shopping Analyzer Dashboard", sections=sections)


def _build_metric_items(state: DashboardState) -> list[dict[str, Any]]:
    return [
        {"label": "Ausgaben gesamt", "value": state.kpis.total_spent},
        {"label": "Ausgaben ohne Rabatte", "value": state.derived.total_before_discount},
        {"label": "Kassenbons gesamt", "value": state.kpis.total_receipts},
        {"label": "Ø Bon-Betrag", "value": state.kpis.avg_receipt},
        {"label": "Pfandrückgabe", "value": state.kpis.total_saved_deposit},
        {"label": "Rabatte gespart", "value": state.kpis.total_discount},
        {"label": "Rabatt-Sparquote", "value": state.derived.discount_pct},
        {"label": "Gesamt-Ersparnis (ohne Pfand)", "value": state.derived.total_savings_no_deposit},
        {"label": "Gesamt-Sparquote", "value": state.derived.total_savings_pct},
    ]
