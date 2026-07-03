# Frontend-Übergang: Streamlit zu Vue

Dieses Dokument beschreibt den aktuellen Frontend-Zustand des Projekts.

## Ziel

Das Dashboard wird als Vue-Frontend betrieben und liest seine Daten aus einer separaten API-Schicht. Die Backend-Seite bereitet weiterhin die fachlichen Kennzahlen auf, das Frontend rendert nur die Sektionen.

## Aufbau

- `frontend/dashboard_state.py` berechnet die Dashboard-Daten.
- `frontend/ui_model.py` formt daraus ein neutrales, sektioniertes Page-Model.
- `frontend/schema.py` serialisiert dieses Model als Vue-freundliches JSON.
- `api/routes/ui.py` stellt `GET /ui/dashboard` bereit.
- `web/` enthält die Vue-App.

## Datenfluss

1. Das Vue-Frontend ruft `GET /ui/dashboard` auf.
2. Das FastAPI-Backend baut daraus ein Dashboard-Page-Model.
3. Das Frontend rendert die gelieferten `sections` nach `kind`.

## Betriebsmodus

- Das Dashboard ist primär read-only.
- Filter lösen nur neue API-Abfragen aus.
- Es gibt keine Client-seitigen Drilldowns oder Modal-Flows in dieser Version.

## Lokaler Start

```bash
cd web
npm install
npm run dev
```

Setze `VITE_API_BASE_URL`, wenn das Backend nicht unter `http://localhost:8000` läuft.
