# Shopping Analyzer

Ein Tool zum Extrahieren, Prüfen und Verwalten von Kassenbons aus Online-Kaufhistorien von **LIDL** und **REWE**.

> [!IMPORTANT]
> Falls du das Projekt aus einem älteren Video oder einer älteren Anleitung kennst: Der Ablauf hat sich geändert. Bitte orientiere dich an den aktuellen CLI- und Menüpfaden in dieser Dokumentation.

## Überblick

Das Projekt unterstützt aktuell zwei Händler:

- **LIDL**: Abruf der digitalen Bons, Parsing, Validierung und Persistierung in `lidl_receipts.json`
- **REWE**: Download der eBon-ZIP, PDF-Extraktion, Parsing, Validierung und Persistierung in `rewe_receipts.json`

Zusätzlich gibt es für beide Händler einen Diagnosepfad für Cookie-/Request-Dateien:

```bash
python get_data.py check --retailer lidl --cookies-file lidl_cookies.json
python get_data.py check --retailer rewe --cookies-file rewe_cookies.json
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
python get_data.py
```

Im Menü kannst du pro Händler zwischen folgenden Aktionen wählen:

1. Initial Setup / Vollimport
2. Update
3. Cookie-Datei prüfen (Diagnose)
4. Zurück

### Direkte CLI-Aufrufe

```bash
python get_data.py initial --retailer lidl --cookies-file lidl_cookies.json
python get_data.py update --retailer lidl --cookies-file lidl_cookies.json
python get_data.py check --retailer lidl --cookies-file lidl_cookies.json

python get_data.py initial --retailer rewe --cookies-file rewe_cookies.json
python get_data.py update --retailer rewe --output-dir tmp/rewe
python get_data.py check --retailer rewe --cookies-file rewe_cookies.json
```

Optional kann das Write-Backend bereits explizit gewählt werden:

```bash
python get_data.py initial --retailer lidl --write-backend json
python get_data.py update --retailer rewe --output-dir tmp/rewe --write-backend json
```

Aktuell ist `json` das einzige verfügbare Backend. Der Schalter ist bereits als Vorbereitung für weitere Write-Backends vorgesehen.

## Händler-spezifische Anleitungen

- [`docs/LIDL_RECEIPTS.md`](./docs/LIDL_RECEIPTS.md) – LIDL-Workflow, Authentifizierung, Limitierungen und Ausgaben
- [`docs/README_REWE_EBONS.md`](./docs/README_REWE_EBONS.md) – REWE-eBon-Workflow, `customerId`, ZIP/PDF-Import und Fehlersuche
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
- der Umschaltpunkt für Write-Backends liegt aktuell im CLI-Entry-Point (`--write-backend`) und wird in die Workflow-Einstiege durchgereicht
- gemeinsame neutrale Bausteine liegen unter `shared/*` sowie in `result_types.py`
- entfernte Wrapper- und Altpfade wie `receipt_schema`, `parsing.receipt_schema`, `parsing.receipt_parse_result` und `diagnostics.*` sollen nicht wieder eingeführt werden

Kanonische Importpfade für neue Beiträge sind insbesondere:

- `shared.receipt_schema`
- `shared.addresses`
- `shared.ports`
- `result_types`

## Ausgaben

Je nach Händler entstehen insbesondere folgende Dateien:

- `lidl_receipts.json`
- `rewe_receipts.json`
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
