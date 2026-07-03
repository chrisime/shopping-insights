"""Public payload schema for the Vue dashboard endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui_model import DashboardPageModel


@dataclass(frozen=True)
class VueDashboardPayload:
    title: str
    sections: list[dict[str, Any]]

    @classmethod
    def from_page_model(cls, page: DashboardPageModel) -> "VueDashboardPayload":
        return cls(title=page.title, sections=[section.to_dict() for section in page.sections])

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "sections": [dict(section) for section in self.sections]}
