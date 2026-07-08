"""Public payload schema for the Vue dashboard endpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from api.services.dashboard_errors import DashboardError
from api.services.ui_model import DashboardPageModel


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
