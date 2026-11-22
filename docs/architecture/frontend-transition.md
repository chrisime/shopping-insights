# Frontend-Übergang

Stand: 2026-07-03

Dieses Dokument beschreibt die neue Zwischenebene zwischen Datenbank und einem künftigen Vue-Frontend.

## Ziel

Die bisherige Streamlit-Auswertung soll schrittweise durch ein Frontend ersetzt werden, ohne die Fachlogik erneut umzubauen.

## Schichten

### 1. `frontend/data_provider.py`

Liefert die Daten entweder aus:

- der SQLite-Datenbank über `MetricsStore`
- oder über die FastAPI-Endpunkte, wenn `API_BASE_URL` gesetzt ist

### 2. `frontend/dashboard_state.py`

Berechnet den fachlichen Zustand des Dashboards:

- KPI-Ladevorgänge
- abgeleitete Kennzahlen
- Zeitreihe
- Wochentagsanalyse
- Top-Artikel

Diese Schicht ist UI-frei und damit sowohl für Streamlit als auch für Vue nutzbar.

### 3. `frontend/ui_model.py`

Beschreibt eine neutrale, serialisierbare Dashboard-Payload.

Wichtige Merkmale:

- eine `DashboardPageModel`
- eine einheitliche `sections`-Liste
- jede Section besitzt `kind`, `title`, `items`
- Convenience-Serializer: `to_dict()`, `from_dict()`, `to_json()`, `from_json()`

### 4. `frontend/schema.py`

Definiert einen expliziten Vue-Vertrag.

Das ist die Schicht, die später direkt aus einer FastAPI-Route als JSON ausgeliefert werden kann.

## Aktueller Status

Heute nutzt `dashboard.py` noch Streamlit.

Der Ablauf ist aber bereits getrennt:

1. Filterwerte werden eingelesen
2. `DashboardState` wird gebaut
3. `DashboardPageModel` wird erzeugt
4. `render_streamlit.py` rendert das Ergebnis

Das ist die Vorstufe für ein Vue-Frontend, das dieselbe Payload konsumiert.

## Spätere Vue-Nutzung

Für Vue ist der geplante Datenfluss:

1. Vue ruft einen Backend-Endpunkt ab
2. Der Endpunkt liefert `VueDashboardPayload` oder ein kompatibles JSON
3. Vue rendert die Sections anhand von `kind`

## Bewusste Verschiebungen

Folgende Punkte sind absichtlich noch nicht umgesetzt:

- CSV-Export
- OpenAPI-Härtung / Doku-Feinschliff

Beides bleibt auf später verschoben, damit die Vue-Vorbereitung nicht aufgebläht wird.
