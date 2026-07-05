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
    min_date: str | None = None
    max_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "sections": [section.to_dict() for section in self.sections],
            "min_date": self.min_date,
            "max_date": self.max_date,
        }


def build_dashboard_page_model(state: DashboardState) -> DashboardPageModel:
    sections = [DashboardSection(kind="metrics", title="Kennzahlen", items=_build_metric_items(state))]

    rewe_items = _build_rewe_bonus_items(state)
    if rewe_items:
        sections.append(DashboardSection(kind="bonus_rewe", title="REWE Bonus", items=rewe_items))

    lidl_items = _build_lidl_bonus_items(state)
    if lidl_items:
        sections.append(DashboardSection(kind="bonus_lidl", title="Lidl Plus Ersparnisse", items=lidl_items))

    total_bonus_items = _build_total_bonus_items(state)
    if total_bonus_items:
        sections.append(DashboardSection(kind="bonus_total", title="Gesamt", items=total_bonus_items))

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
    return DashboardPageModel(
        title="Shopping Analyzer Dashboard",
        sections=sections,
        min_date=_date_text(state.min_date),
        max_date=_date_text(state.max_date),
    )


def _build_metric_items(state: DashboardState) -> list[dict[str, Any]]:
    return [
        {"label": "Ausgaben gesamt", "value": _currency(state.kpis.total_spent)},
        {"label": "Ausgaben ohne Rabatte", "value": _currency(state.derived.total_before_discount)},
        {"label": "Kassenbons gesamt", "value": str(state.kpis.total_receipts)},
        {"label": "Ø Bon-Betrag", "value": _currency(state.kpis.avg_receipt)},
        {"label": "Pfandrückgabe", "value": _currency(state.kpis.total_saved_deposit)},
        {"label": "Rabatte gespart", "value": _currency(state.kpis.total_discount)},
        {"label": "Rabatt-Sparquote", "value": _percent(state.derived.discount_pct)},
        {"label": "Gesamt-Ersparnis (ohne Pfand)", "value": _currency(state.derived.total_savings_no_deposit)},
        {"label": "Gesamt-Sparquote", "value": _percent(state.derived.total_savings_pct)},
    ]


def _build_rewe_bonus_items(state: DashboardState) -> list[dict[str, Any]]:
    items = []
    if state.retailer in (None, "rewe") and (state.bonus_kpis.rewe_bonus_collected > 0 or state.bonus_kpis.rewe_bonus_balance > 0):
        items.append({"label": "Bonus gesammelt (Zeitraum)", "value": _currency(state.bonus_kpis.rewe_bonus_collected)})
        items.append({"label": "Bonus Guthaben (aktuell)", "value": _currency(state.bonus_kpis.rewe_bonus_balance)})
    return items


def _build_lidl_bonus_items(state: DashboardState) -> list[dict[str, Any]]:
    items = []
    if state.retailer in (None, "lidl") and (state.bonus_kpis.lidlplus_discount > 0 or state.bonus_kpis.sticker_discount > 0):
        items.append({"label": "Lidl Plus gespart", "value": _currency(state.bonus_kpis.lidlplus_discount)})
        items.append({"label": "Lidl Plus Sparquote", "value": _percent(_pct(state.bonus_kpis.lidlplus_discount, state.kpis.total_spent))})
        items.append({"label": "Sticker-Rabatte", "value": _currency(state.bonus_kpis.sticker_discount)})
        items.append({"label": "Sticker-Sparquote", "value": _percent(_pct(state.bonus_kpis.sticker_discount, state.kpis.total_spent))})
    return items


def _build_total_bonus_items(state: DashboardState) -> list[dict[str, Any]]:
    total_bonus_redeemed = state.derived.total_bonus_redeemed
    if total_bonus_redeemed <= 0:
        return []
    return [
        {"label": "Bonus eingelöst", "value": _currency(total_bonus_redeemed)},
        {"label": "Bonus-Sparquote", "value": _percent(state.derived.bonus_redeemed_pct)},
    ]


def _currency(value: float) -> str:
    return f"€{value:,.2f}"


def _percent(value: float) -> str:
    return f"{value:.1f}%"


def _pct(value: float, total: float) -> float:
    if not total:
        return 0.0
    return round((value / total) * 100, 2)


def _date_text(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
