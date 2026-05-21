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

- [`docs/LIDL_RECEIPTS.md`](./docs/LIDL_RECEIPTS.md) – LIDL-Workflow, Authentifizierung, Limitierungen und Ausgaben
- [`docs/README_REWE_EBONS.md`](./docs/README_REWE_EBONS.md) – REWE-eBon-Workflow, `customerId`, ZIP/PDF-Import und Fehlersuche
- [`docs/README_DATA_HARMONIZATION.md`](./docs/README_DATA_HARMONIZATION.md) – Stand und Unterschiede der Harmonisierung zwischen LIDL und REWE
- [`docs/LIBREWOLF_SESSION_COOKIES.md`](./docs/LIBREWOLF_SESSION_COOKIES.md) – ergänzende Hinweise zur Cookie-Gewinnung aus LibreWolf

## Architektur und Beitragshinweise

Für neue Änderungen gelten explizite Paket- und Workflow-Regeln. Der empfohlene Einstieg ist:

1. [`docs/architecture/code-reading-guide.md`](./docs/architecture/code-reading-guide.md)
2. [`docs/architecture/package-layer-rules.md`](./docs/architecture/package-layer-rules.md)
3. [`docs/architecture/workflow-overview.md`](./docs/architecture/workflow-overview.md)
4. [`docs/adr/README.md`](./docs/adr/README.md)
5. [`docs/adr/0003-package-layer-rules-and-wrapper-removal.md`](./docs/adr/0003-package-layer-rules-and-wrapper-removal.md)

Wichtige Kurzfassung:

- `workflows/*` ist die einzige Orchestrierungsschicht
- `workflows/pipeline_runner.py` arbeitet nur mit injizierten Funktionen/Ports, nicht mit konkreten Parsing- oder Storage-Adaptern
- Persistenz erfolgt standardmäßig DB-first nach `shopping_receipts.sqlite`; externe Formate werden über Export-Adapter erzeugt
- gemeinsame neutrale Bausteine liegen unter `shared/*` sowie in `result_types.py`
- entfernte Wrapper- und Altpfade wie `receipt_schema`, `parsing.receipt_schema`, `parsing.receipt_parse_result` und `diagnostics.*` sollen nicht wieder eingeführt werden

Kanonische Importpfade für neue Beiträge sind insbesondere:

- `shared.receipt_schema`
- `shared.addresses`
- `shared.ports`
- `result_types`

## Ausgaben

Je nach Workflow entstehen insbesondere folgende Dateien:

- `shopping_receipts.sqlite`
- optionale Exporte: `lidl_receipts.json`, `rewe_receipts.json`
- `tmp/rewe/receipts.zip`
- `tmp/rewe/pdfs/`

## Dashboard

Nach dem Import kannst du die gesammelten Daten im Dashboard ansehen:

```bash
streamlit run dashboard.py
```

Danach ist das Dashboard typischerweise unter `http://localhost:8501` erreichbar.

## Sicherheitshinweise

Cookie- und Request-Dateien enthalten sensible Authentifizierungsdaten.

- niemals committen
- niemals weitergeben
- lokal sicher speichern
- nach Möglichkeit nach erfolgreicher Nutzung wieder löschen

## Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPL-3.0)**.

Die vollständigen Lizenzbedingungen stehen in [`LICENCE.md`](./LICENCE.md).
