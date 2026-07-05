"""Streamlit rendering helpers for the dashboard page model."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from .ui_model import DashboardPageModel


def render_dashboard_page_model(page: DashboardPageModel, st_module: Any = st) -> None:
    st_module.title(page.title)

    for section in page.sections:
        st_module.markdown(f"##### {section.title}")
        if not section.items:
            st_module.info("Keine Daten für den gewählten Zeitraum.")
            continue

        if section.kind == "metrics":
            cols = st_module.columns(len(section.items))
            for col, metric in zip(cols, section.items):
                col.metric(metric["label"], metric["value"])
            continue

        df = pd.DataFrame(section.items)
        if section.kind == "chart" and section.title == "Einkaufsverhalten nach Wochentag" and {"Wochentag", "Einkäufe", "Ø Ausgaben (€)"}.issubset(df.columns):
            cols = st_module.columns(2)
            cols[0].bar_chart(df.set_index("Wochentag")["Einkäufe"])
            cols[1].bar_chart(df.set_index("Wochentag")["Ø Ausgaben (€)"])
            continue

        if section.kind == "chart":
            value_column = _select_value_column(df)
            if value_column is None:
                st_module.dataframe(df, width="stretch", hide_index=True)
            else:
                index_column = _select_index_column(df)
                if index_column is None:
                    st_module.bar_chart(df[value_column])
                else:
                    st_module.bar_chart(df.set_index(index_column)[value_column])
            continue

        st_module.dataframe(df, width="stretch", hide_index=True)


def _select_value_column(df: pd.DataFrame) -> str | None:
    preferred = ["Ausgaben (€)", "Einkäufe", "total_spent", "receipt_count"]
    for column in preferred:
        if column in df.columns:
            return column
    numeric_columns = [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]
    return numeric_columns[0] if numeric_columns else None


def _select_index_column(df: pd.DataFrame) -> str | None:
    preferred = ["Zeitraum", "Wochentag", "Artikel", "name", "period"]
    for column in preferred:
        if column in df.columns:
            return column
    return str(df.columns[0]) if len(df.columns) > 1 else None
