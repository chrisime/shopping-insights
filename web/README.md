# Vue Dashboard

Dieses Verzeichnis enthält das Vue-Frontend für das Shopping-Analyzer-Dashboard.

## Start

```bash
pnpm install
pnpm dev
```

Wenn das FastAPI-Backend nicht auf `http://localhost:8000` läuft, setze:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Qualitätssicherung

Vite+ (`vp`) ist der Frontend-Toolchain; die pnpm-Scripts rufen `vp` auf.

```bash
pnpm exec vp check          # Format, Lint und Typecheck (tsgo/tsrs)
pnpm exec vp run typecheck  # Typecheck der Vue-SFCs (vue-tsc)
```

TypeScript ist für `vue-tsc` auf 6.0.x gepinnt; `vp check` nutzt unabhängig davon das gebündelte tsrs.

**Wichtig:** `vp` muss aus `web/node_modules/.bin` kommen. Ein global installiertes `vp` bringt seine eigene Vitest-Kopie mit, die projektspezifische Abhängigkeiten wie `jsdom` nicht findet. Dann laufen nur die Node-Tests; alle jsdom-Suiten enden mit `Cannot find package 'jsdom'` als „unhandled errors“ (`4 passed`, `13 passed`, `12 errors`). Absicherung:

```bash
pnpm exec vp test      # nutzt immer die Projektversion
```

## Tests

```bash
pnpm test
# einmalig ausführen:
pnpm exec vp test run
```

### Produktions-Integrationstest

Installiere einmalig Chromium für Playwright und führe den Integrationstest in `web/` aus.
Der Test baut das Dashboard, startet FastAPI und prüft die komprimierte Auslieferung sowie
das Laden von ECharts beim Öffnen des Trend-Tabs.

```bash
pnpm exec playwright install --only-shell chromium
pnpm test:integration
```

## Produktionsbuild und Auslieferung

Erzeuge den Produktionsbuild aus dem Projektverzeichnis und starte danach das FastAPI-Backend.

```bash
(cd web && pnpm install && pnpm build)
uv run --locked start-backend
```

Öffne `http://127.0.0.1:8000/`. FastAPI liefert die Vue-Startseite und die Assets aus
`web/dist/` aus. Ein Vite-Plugin erzeugt beim Build Brotli- und gzip-Dateien für JavaScript und CSS. FastAPI
wählt anhand von `Accept-Encoding` eine verfügbare Variante. Kopiere beim Deployment
das gesamte `web/dist/`-Verzeichnis einschließlich der komprimierten Dateien.

Der Produktionsbuild nutzt standardmäßig dieselbe Origin wie das Dashboard für die API.
Für ein separates Backend kannst du beim Build weiterhin `VITE_API_BASE_URL` setzen.

## API

Das Frontend liest das Dashboard über `GET /ui/dashboard`.
Der Export-Button lädt die aktuell gefilterten Belege als JSON über `GET /exports/receipts` herunter.

## Rossmann-Import

Öffne **Import**, wähle **Rossmann** als Händler und **Rossmann-Konto** zur Anmeldung. Der Import übernimmt neue Filialbons samt Artikeln. Fortschritt und Ergebnis erscheinen im Importbereich. Unter **Ausgaben** und **Artikel** kannst du die importierten Daten nach Rossmann filtern.

Das Dashboard startet den Vorgang über `POST /imports/start` und verfolgt ihn über `GET /imports/{job_id}/events`. Für die Kontoanmeldung verwendet das Frontend HTTPS oder eine lokale HTTP-Verbindung zum Backend. [Rossmann-Anleitung](../README_ROSSMANN_RECEIPTS.md)
