"""Streamlit Dashboard – Phase 1 KPIs from SQLite database.

Launch with:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from metrics import MetricsStore

# --- Page config ---
st.set_page_config(layout="wide", page_title="Shopping Analyzer Dashboard", page_icon="🛒")

# --- Custom CSS ---
st.markdown("""
<style>
.main .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- Check DB exists ---
DB_FILE = "shopping_receipts.sqlite"
if not Path(DB_FILE).exists():
    st.error(f"Datenbank '{DB_FILE}' nicht gefunden. Bitte zuerst Daten importieren.")
    st.stop()

store = MetricsStore()

# --- Sidebar: Filters ---
st.sidebar.header("Filter")

# Retailer selection
retailer_options = {"Alle": None, "Lidl": "lidl", "REWE": "rewe"}
selected_retailer_label = st.sidebar.selectbox("Händler", list(retailer_options.keys()))
selected_retailer = retailer_options[selected_retailer_label]

# Date range – determine available range first
all_kpis = store.basic_kpis(retailer=selected_retailer)

if all_kpis.total_receipts == 0:
    st.warning("Keine Kassenbons in der Datenbank gefunden.")
    st.stop()

min_date = pd.to_datetime(all_kpis.min_date).date()
max_date = pd.to_datetime(all_kpis.max_date).date()

start_date = st.sidebar.date_input("Startdatum", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("Enddatum", max_date, min_value=min_date, max_value=max_date)

start_str = str(start_date)
end_str = str(end_date)

# --- Filtered KPIs ---
kpis = store.basic_kpis(retailer=selected_retailer, start_date=start_str, end_date=end_str)
bonus_kpis = store.retailer_bonus_kpis(retailer=selected_retailer, start_date=start_str, end_date=end_str)

# --- Title ---
st.title("🛒 Shopping Analyzer Dashboard")

# --- Grundkennzahlen ---
st.header("Kennzahlen")
st.markdown("##### Grunddaten")
total_before_discount = kpis.total_spent + kpis.total_discount + bonus_kpis.rewe_bonus_redeemed + bonus_kpis.lidlplus_discount + bonus_kpis.sticker_discount
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ausgaben gesamt", f"€{kpis.total_spent:,.2f}")
col2.metric("Ausgaben ohne Rabatte", f"€{total_before_discount:,.2f}")
col3.metric("Kassenbons gesamt", f"{kpis.total_receipts}")
col4.metric("Ø Bon-Betrag", f"€{kpis.avg_receipt:,.2f}")

st.markdown("##### Pfandrückgabe")
col1, _ = st.columns(2)
col1.metric("Pfand gespart", f"€{kpis.total_saved_deposit:,.2f}")

st.markdown("##### Ersparnisse")
# Rabatt-Sparquote (nur reguläre Rabatte, ohne Pfand)
discount_pct = (kpis.total_discount / kpis.total_spent * 100) if kpis.total_spent > 0 else 0
# Bonus-Sparquote (eingelöstes Bonus-Guthaben)
total_bonus_redeemed = bonus_kpis.rewe_bonus_redeemed + bonus_kpis.lidlplus_discount + bonus_kpis.sticker_discount
bonus_pct = (total_bonus_redeemed / kpis.total_spent * 100) if kpis.total_spent > 0 else 0
# Gesamt-Sparquote (Rabatte + eingelöstes Bonus-Guthaben, ohne Pfand)
total_savings_no_deposit = kpis.total_discount + total_bonus_redeemed
total_savings_pct = (total_savings_no_deposit / kpis.total_spent * 100) if kpis.total_spent > 0 else 0

col1, col2 = st.columns(2)
col1.metric("Rabatte gespart", f"€{kpis.total_discount:,.2f}")
col2.metric("Rabatt-Sparquote", f"{discount_pct:.1f}%")

if total_bonus_redeemed > 0 and selected_retailer == "rewe":
    st.markdown("##### Bonus")
    col1, col2 = st.columns(2)
    col1.metric("Bonus eingelöst", f"€{total_bonus_redeemed:,.2f}")
    col2.metric("Bonus-Sparquote", f"{bonus_pct:.1f}%")

# Retailer-specific bonus section
show_rewe_bonus = selected_retailer is None or selected_retailer == "rewe"
show_lidl_bonus = selected_retailer is None or selected_retailer == "lidl"

if show_rewe_bonus and (bonus_kpis.rewe_bonus_collected > 0 or bonus_kpis.rewe_bonus_balance > 0):
    st.markdown("##### REWE Bonus")
    col1, col2 = st.columns(2)
    col1.metric("Bonus gesammelt (Zeitraum)", f"€{bonus_kpis.rewe_bonus_collected:,.2f}")
    col2.metric("Bonus Guthaben (aktuell)", f"€{bonus_kpis.rewe_bonus_balance:,.2f}")

if show_lidl_bonus and (bonus_kpis.lidlplus_discount > 0 or bonus_kpis.sticker_discount > 0):
    st.markdown("##### Lidl Plus Ersparnisse")
    col1, col2 = st.columns(2)
    col1.metric("Lidl Plus gespart", f"€{bonus_kpis.lidlplus_discount:,.2f}")
    lidlplus_pct = (bonus_kpis.lidlplus_discount / kpis.total_spent * 100) if kpis.total_spent > 0 else 0
    col2.metric("Lidl Plus Sparquote", f"{lidlplus_pct:.1f}%")

    col1, col2 = st.columns(2)
    col1.metric("Sticker-Rabatte", f"€{bonus_kpis.sticker_discount:,.2f}")
    sticker_pct = (bonus_kpis.sticker_discount / kpis.total_spent * 100) if kpis.total_spent > 0 else 0
    col2.metric("Sticker-Sparquote", f"{sticker_pct:.1f}%")

st.markdown("##### Gesamt")
col1, col2 = st.columns(2)
col1.metric("Gesamt-Ersparnis (ohne Pfand)", f"€{total_savings_no_deposit:,.2f}")
col2.metric("Gesamt-Sparquote", f"{total_savings_pct:.1f}%")

st.markdown("---")

# --- Ausgaben über Zeit ---
st.header("Ausgaben über Zeit")

time_granularity = st.radio(
    "Zeitgranularität:",
    ["Täglich", "Monatlich", "Jährlich"],
    horizontal=True,
    key="time_granularity",
)

if time_granularity == "Täglich":
    ts_data = store.spending_by_day(retailer=selected_retailer, start_date=start_str, end_date=end_str)
elif time_granularity == "Monatlich":
    ts_data = store.spending_by_month(retailer=selected_retailer, start_date=start_str, end_date=end_str)
else:
    ts_data = store.spending_by_year(retailer=selected_retailer, start_date=start_str, end_date=end_str)

if ts_data:
    ts_df = pd.DataFrame([{"Zeitraum": r.period, "Ausgaben (€)": r.total_spent, "Einkäufe": r.receipt_count} for r in ts_data])
    ts_df = ts_df.set_index("Zeitraum")

    spending_view = st.radio("Ansicht:", ["Absolut", "Kumulativ"], horizontal=True, key="spending_view")

    if spending_view == "Kumulativ":
        ts_df["Ausgaben (€)"] = ts_df["Ausgaben (€)"].cumsum()

    st.bar_chart(ts_df["Ausgaben (€)"])

    # Summary stats
    if spending_view == "Absolut":
        col1, col2, col3 = st.columns(3)
        col1.metric("Ø Ausgaben pro Zeitraum", f"€{ts_df['Ausgaben (€)'].mean():.2f}")
        col2.metric("Maximum", f"€{ts_df['Ausgaben (€)'].max():.2f}")
        col3.metric("Minimum", f"€{ts_df['Ausgaben (€)'].min():.2f}")
else:
    st.info("Keine Daten für den gewählten Zeitraum.")

st.markdown("---")

# --- Wochentag-Analyse ---
st.header("Einkaufsverhalten nach Wochentag")

weekday_data = store.weekday_analysis(retailer=selected_retailer, start_date=start_str, end_date=end_str)

if weekday_data:
    weekday_order = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    wd_df = pd.DataFrame([
        {"Wochentag": r.weekday_name, "Einkäufe": r.trip_count, "Ø Ausgaben (€)": round(r.avg_spent, 2), "Gesamt (€)": round(r.total_spent, 2)}
        for r in weekday_data
    ])
    wd_df["Wochentag"] = pd.Categorical(wd_df["Wochentag"], categories=weekday_order, ordered=True)
    wd_df = wd_df.sort_values("Wochentag").set_index("Wochentag")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Anzahl Einkäufe")
        st.bar_chart(wd_df["Einkäufe"])
    with col2:
        st.markdown("##### Ø Ausgaben pro Einkauf")
        st.bar_chart(wd_df["Ø Ausgaben (€)"])
else:
    st.info("Keine Daten für die Wochentag-Analyse.")

st.markdown("---")

# --- Top-Artikel ---
st.header("Top-Artikel")

top_view = st.radio("Sortieren nach:", ["Menge", "Ausgaben"], horizontal=True, key="top_view")
top_limit = st.slider("Anzahl anzeigen", min_value=5, max_value=50, value=20, step=5)

if top_view == "Menge":
    top_data = store.top_items_by_quantity(retailer=selected_retailer, start_date=start_str, end_date=end_str, limit=top_limit)
else:
    top_data = store.top_items_by_spend(retailer=selected_retailer, start_date=start_str, end_date=end_str, limit=top_limit)

if top_data:
    def format_qty(row):
        if row["Einheit"] == "kg":
            return f"{row['Menge']:.3f} {row['Einheit']}"
        return f"{int(row['Menge'])} {row['Einheit']}"

    top_df = pd.DataFrame([
        {
            "Artikel": r.name,
            "Menge": r.total_quantity,
            "Einheit": r.unit,
            "Ausgaben (€)": round(r.total_spent, 2),
            "Einkäufe": r.purchase_count,
        }
        for r in top_data
    ])
    top_df["Gesamtmenge"] = top_df.apply(format_qty, axis=1)

    display_cols = ["Artikel", "Gesamtmenge", "Ausgaben (€)", "Einkäufe"]
    st.dataframe(top_df[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("Keine Artikeldaten für den gewählten Zeitraum.")
