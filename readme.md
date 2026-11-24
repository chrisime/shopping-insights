# Shopping Analyzer

Ein Tool zum Abrufen, Prüfen und Auswerten digitaler Kassenbons von **LIDL**, **REWE**, **dm** und **Rossmann**.

> [!IMPORTANT]
> Falls du das Projekt aus einem älteren Video oder einer älteren Anleitung kennst: Der Ablauf hat sich geändert. Bitte orientiere dich an den aktuellen CLI- und Menüpfaden in dieser Dokumentation.

## Überblick

Das Projekt unterstützt vier Händler.

- **LIDL**: Abruf der digitalen Bons, Parsing, Validierung und Persistierung in `shopping_receipts.sqlite`
- **REWE**: Download der eBon-ZIP, PDF-Extraktion, Parsing, Validierung und Persistierung in `shopping_receipts.sqlite`
- **dm**: Abruf der Kaufhistorie (Markt-eBons) über die dm-API, Parsing, Validierung und Persistierung in `shopping_receipts.sqlite`
- **Rossmann**: Abruf digitaler Filialbons samt Artikeln über anybill und Import in `shopping_receipts.sqlite`

JSON-Dateien sind ein **Exportformat** aus dem aktuellen DB-Stand.

Zusätzlich gibt es für alle Händler einen Diagnosepfad für Cookie-/Request-Dateien:

```bash
uv run --locked python fetch_tickets.py check --retailer lidl --cookies-file lidl_cookies.json
uv run --locked python fetch_tickets.py check --retailer rewe --cookies-file rewe_cookies.json
uv run --locked python fetch_tickets.py check --retailer dm --cookies-file dm_cookies.json
uv run --locked python fetch_tickets.py check --retailer rossmann --cookies-file rossmann_cookies.json
```

## Voraussetzungen

- Python 3.11 oder neuer und uv
- mit `uv sync --locked` installierte Projekt-Abhängigkeiten
- ein aktives Konto beim gewünschten Händler
- für Lidl, REWE und dm ein unterstütztes Browserprofil oder eine exportierte Cookie-/Request-Datei
- für Rossmann die Zugangsdaten des Kontos, das in der Rossmann-App die Filialbons anzeigt

Installation:

```bash
git clone <repository-url>
cd shopping-analyzer
uv sync --locked
```

## Schnellstart

### Interaktives Menü

```bash
uv run --locked python fetch_tickets.py
```

Im Menü kannst du je nach Händler folgende Aktionen wählen:

- **LIDL**: Sync, JSON aus DB erzeugen, Cookie-Datei prüfen
- **REWE**: Initial, Update, JSON aus DB erzeugen, Cookie-/Request-Datei prüfen
- **dm**: Initial, Update, JSON aus DB erzeugen, Cookie-Datei prüfen
- **Rossmann**: Online-Abruf, lokaler Import, JSON-Export und Cookie-Datei-Diagnose

### Direkte CLI-Aufrufe

```bash
uv run --locked python fetch_tickets.py initial --retailer lidl --cookies-file lidl_cookies.json
uv run --locked python fetch_tickets.py update --retailer lidl --cookies-file lidl_cookies.json
uv run --locked python fetch_tickets.py check --retailer lidl --cookies-file lidl_cookies.json
uv run --locked python fetch_tickets.py export --retailer lidl --output-file lidl_receipts.json

uv run --locked python fetch_tickets.py initial --retailer rewe --cookies-file rewe_cookies.json
uv run --locked python fetch_tickets.py update --retailer rewe --output-dir tmp/rewe
uv run --locked python fetch_tickets.py check --retailer rewe --cookies-file rewe_cookies.json
uv run --locked python fetch_tickets.py export --retailer rewe --output-file rewe_receipts.json

uv run --locked python fetch_tickets.py initial --retailer dm --cookies-file dm_cookies.json
uv run --locked python fetch_tickets.py update --retailer dm --output-dir tmp/dm
uv run --locked python fetch_tickets.py check --retailer dm --cookies-file dm_cookies.json
uv run --locked python fetch_tickets.py export --retailer dm --output-file dm_receipts.json

uv run --locked python fetch_tickets.py initial --retailer rossmann --login
uv run --locked python fetch_tickets.py update --retailer rossmann --output-dir tmp/rossmann
uv run --locked python fetch_tickets.py export --retailer rossmann --output-file rossmann_receipts.json
```

## Händler-spezifische Anleitungen

- [`docs/LIBREWOLF_SESSION_COOKIES.md`](./docs/LIBREWOLF_SESSION_COOKIES.md) – ergänzende Hinweise zur Cookie-Gewinnung aus LibreWolf
- [`README_LIDL_RECEIPTS.md`](./README_LIDL_RECEIPTS.md) – LIDL-Kassenbons abrufen und importieren
- [`README_REWE_EBONS.md`](./README_REWE_EBONS.md) – REWE-eBons herunterladen und importieren
- [`README_DM_EBONS.md`](./README_DM_EBONS.md) – dm-Kaufhistorie abrufen und importieren (OAuth-Flow, Cookie-Export, CLI)
- [`README_ROSSMANN_RECEIPTS.md`](./README_ROSSMANN_RECEIPTS.md) – Rossmann-Filialbons im Dashboard oder per CLI abrufen

### dm – Cookie-Export für den OAuth-Flow

dm authentifiziert sich über einen OAuth-2.0-Flow mit PKCE gegen `signin.dm.de`. Der Abruf benötigt eine exportierte Cookie-Datei, die **mindestens die dm-Session-Cookies** enthält (z. B. `_SI_SID_*` auf `.dm.de` sowie die `signin.dm.de`-Session-Cookies). Ohne eine gültige dm-Session kann kein kurzfristiger Access-Token erstellt werden (`fetch_tickets.py check --retailer dm` zeigt eine Ampel-Diagnose). Ausführliche Schritte stehen in [`README_DM_EBONS.md`](./README_DM_EBONS.md).

## Ausgaben

Je nach Workflow entstehen insbesondere folgende Dateien:

- `shopping_receipts.sqlite`
- optionale Exporte: `lidl_receipts.json`, `rewe_receipts.json`, `dm_receipts.json`, `rossmann_receipts.json`
- `tmp/rewe/receipts.zip`
- `tmp/rewe/pdfs/`
- `tmp/dm/ebons/` (eBon-JSONs), `tmp/dm/pdf/` (eBon-PDFs)
- `tmp/rossmann/receipts/` (anybill-Detail-JSONs), `tmp/rossmann/pdf/` (verfügbare Original-PDFs)

## Dashboard

Starte das FastAPI-Backend im Projektverzeichnis.

```bash
uv run --locked start-backend
```

Starte das Vue-Dashboard in einem zweiten Terminal.

```bash
cd web
pnpm install
pnpm dev
```

Das Frontend liest Daten über `GET /ui/dashboard` vom FastAPI-Backend.
Über den Export-Button kannst du die aktuell gefilterten Tickets als JSON über `GET /exports/receipts` herunterladen.
Setze dafür bei Bedarf `VITE_API_BASE_URL`, zum Beispiel auf `http://localhost:8000`.

Details und Projektkontext stehen in [`web/README.md`](./web/README.md).

Für einen Rossmann-Abruf wähle im Dashboard **Import → Rossmann → Rossmann-Konto**. Die Anmeldung gilt für den jeweiligen Abruf. Für später hinzugekommene Filialbons startest du denselben Import erneut. [Rossmann-Anleitung](./README_ROSSMANN_RECEIPTS.md)

Aktuell bewusst noch nicht umgesetzt:

- CSV-Export
- OpenAPI-Dokumentation / Härtung

## Sicherheitshinweise

Cookie- und Request-Dateien enthalten sensible Authentifizierungsdaten.

- niemals committen
- niemals weitergeben
- lokal sicher speichern
- nach Möglichkeit nach erfolgreicher Nutzung wieder löschen

## Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Die vollständigen Lizenzbedingungen stehen in [`LICENCE.md`](./LICENCE.md).
