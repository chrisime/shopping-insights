"""Public payload schema for the Vue dashboard endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.dashboard_errors import DashboardError
from frontend.ui_model import DashboardPageModel


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
        payload = {
            "title": self.title,
            "sections": [dict(section) for section in self.sections],
            "min_date": self.min_date,
            "max_date": self.max_date,
        }
        if self.error is not None:
            payload["error"] = {"error_code": self.error.error_code, "detail": self.error.detail}
        return payload
