# Shopping Analyzer

Ein Tool zum Extrahieren, Prüfen und Verwalten von Kassenbons aus Online-Kaufhistorien von **LIDL** und **REWE**.

> [!IMPORTANT]
> Falls du das Projekt aus einem älteren Video oder einer älteren Anleitung kennst: Der Ablauf hat sich geändert. Bitte orientiere dich an den aktuellen CLI- und Menüpfaden in dieser Dokumentation.

## Überblick

Das Projekt unterstützt aktuell zwei Händler:

- **LIDL**: Abruf der digitalen Bons, Parsing, Validierung und Persistierung in `shopping_receipts.sqlite`
- **REWE**: Download der eBon-ZIP, PDF-Extraktion, Parsing, Validierung und Persistierung in `shopping_receipts.sqlite`

JSON-Dateien sind ein **Exportformat** aus dem aktuellen DB-Stand.

Zusätzlich gibt es für beide Händler einen Diagnosepfad für Cookie-/Request-Dateien:

```bash
python fetch_tickets.py check --retailer lidl --cookies-file lidl_cookies.json
python fetch_tickets.py check --retailer rewe --cookies-file rewe_cookies.json
```

## Voraussetzungen

- Python 3.10 oder neuer
- installierte Projekt-Abhängigkeiten aus `requirements.txt`
- ein aktives LIDL- oder REWE-Konto
- entweder ein unterstütztes Browserprofil oder eine exportierte Cookie-/Request-Datei

Installation:

```bash
git clone <repository-url>
cd shopping-analyzer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Unter Windows:

```cmd
venv\Scripts\activate
```

## Schnellstart

### Interaktives Menü

```bash
python fetch_tickets.py
```

Im Menü kannst du je nach Händler folgende Aktionen wählen:

- **LIDL**: Sync, JSON aus DB erzeugen, Cookie-Datei prüfen
- **REWE**: Initial, Update, JSON aus DB erzeugen, Cookie-/Request-Datei prüfen

### Direkte CLI-Aufrufe

```bash
python fetch_tickets.py initial --retailer lidl --cookies-file lidl_cookies.json
python fetch_tickets.py update --retailer lidl --cookies-file lidl_cookies.json
python fetch_tickets.py check --retailer lidl --cookies-file lidl_cookies.json
python fetch_tickets.py export --retailer lidl --output-file lidl_receipts.json

python fetch_tickets.py initial --retailer rewe --cookies-file rewe_cookies.json
python fetch_tickets.py update --retailer rewe --output-dir tmp/rewe
python fetch_tickets.py check --retailer rewe --cookies-file rewe_cookies.json
python fetch_tickets.py export --retailer rewe --output-file rewe_receipts.json
```

Optional kann für den Export ein alternativer DB-Pfad gesetzt werden:

```bash
python fetch_tickets.py export --retailer rewe --db-path shopping_receipts.sqlite --output-file rewe_receipts.json
```

## Händler-spezifische Anleitungen

- [`docs/LIBREWOLF_SESSION_COOKIES.md`](./docs/LIBREWOLF_SESSION_COOKIES.md) – ergänzende Hinweise zur Cookie-Gewinnung aus LibreWolf

## Ausgaben

Je nach Workflow entstehen insbesondere folgende Dateien:

- `shopping_receipts.sqlite`
- optionale Exporte: `lidl_receipts.json`, `rewe_receipts.json`
- `tmp/rewe/receipts.zip`
- `tmp/rewe/pdfs/`

## Dashboard

Nach dem Import kannst du die gesammelten Daten im Vue-Dashboard ansehen:

```bash
cd web
npm install
npm run dev
```

Das Frontend liest Daten über `GET /ui/dashboard` vom FastAPI-Backend.
Über den Export-Button kannst du die aktuell gefilterten Tickets als JSON über `GET /exports/receipts` herunterladen.
Setze dafür bei Bedarf `VITE_API_BASE_URL`, zum Beispiel auf `http://localhost:8000`.

Details und Projektkontext stehen in [`web/README.md`](./web/README.md).

Wenn `API_BASE_URL` gesetzt ist, bezieht das Dashboard seine Daten über die FastAPI-Schicht statt direkt aus SQLite.

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
