"""Streamlit Dashboard – Phase 1 KPIs from SQLite database.

Launch with:
    streamlit run dashboard.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from frontend.dashboard_state import build_dashboard_state
from frontend.data_provider import get_dashboard_data_provider
from frontend.render_streamlit import render_dashboard_page_model
from frontend.ui_model import build_dashboard_page_model


st.set_page_config(layout="wide", page_title="Shopping Analyzer Dashboard", page_icon="🛒")

st.markdown(
    """
<style>
.main .block-container { padding-top: 2rem; }
</style>
""",
    unsafe_allow_html=True,
)

DB_FILE = "shopping_receipts.sqlite"
if not Path(DB_FILE).exists():
    st.error(f"Datenbank '{DB_FILE}' nicht gefunden. Bitte zuerst Daten importieren.")
    st.stop()

provider = get_dashboard_data_provider()

st.sidebar.header("Filter")

retailer_options = {"Alle": None, "Lidl": "lidl", "REWE": "rewe"}
selected_retailer_label = st.sidebar.selectbox("Händler", list(retailer_options.keys()))
selected_retailer = retailer_options[selected_retailer_label]

all_kpis = provider.basic_kpis(retailer=selected_retailer)
if all_kpis.total_receipts == 0:
    st.warning("Keine Kassenbons in der Datenbank gefunden.")
    st.stop()

if all_kpis.min_date is None or all_kpis.max_date is None:
    st.warning("Keine gültigen Datumswerte in der Datenbank gefunden.")
    st.stop()

min_date = pd.to_datetime(all_kpis.min_date).date()
max_date = pd.to_datetime(all_kpis.max_date).date()

start_date = st.sidebar.date_input("Startdatum", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Enddatum", max_date, min_value=min_date, max_value=max_date)

time_granularity = st.radio(
    "Zeitgranularität:",
    ["Täglich", "Monatlich", "Jährlich"],
    horizontal=True,
    key="time_granularity",
)
spending_view = st.radio("Ansicht:", ["Absolut", "Kumulativ"], horizontal=True, key="spending_view")
top_view = st.radio("Sortieren nach:", ["Menge", "Ausgaben"], horizontal=True, key="top_view")
top_limit = st.slider("Anzahl anzeigen", min_value=5, max_value=50, value=20, step=5)

try:
    dashboard_state = build_dashboard_state(
        provider,
        retailer=selected_retailer,
        start_date=str(start_date),
        end_date=str(end_date),
        time_granularity=time_granularity,
        spending_view=spending_view,
        top_view=top_view,
        top_limit=top_limit,
    )
except ValueError:
    st.warning("Keine Kassenbons in der Datenbank gefunden.")
    st.stop()

page = build_dashboard_page_model(dashboard_state)
render_dashboard_page_model(page, st_module=st)
