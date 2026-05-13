# Workflow-Überblick

Stand: 2026-05-10

Dieses Dokument beschreibt die fachlichen Hauptabläufe in `workflows/*` in einer kompakteren Form als Einstieg für Wartung und Refactoring.

## Grundidee

`workflows/*` ist die einzige Orchestrierungsschicht.

Öffentlich gemacht werden dort nur echte Einstiegspunkte:

- Use Cases wie `run_lidl_initial(...)` oder `run_rewe_update(...)`
- bewusst freigegebene Diagnose-/Import-Helfer wie `fetch_lidl_receipt_parse_result(...)` oder `parse_rewe_receipt_pdf_with_result(...)`

Alle übrigen Orchestrierungshelfer bleiben privat und beginnen mit `_`.

Die Workflows kombinieren:
- `auth/*` für Session-/Auth-Quellen
- `api/*` für Transport
- `parsing/*` für Extraktion
- `storage/*` für Persistenz
- `reporting/*` für Ausgabe
- `shared/*` / `result_types.py` für neutrale Kernbausteine

## Gemeinsame Pipeline-Idee

Die lineare Standardpipeline besteht aus:

1. **Rohdaten bereitstellen**
2. **parsen**
3. **validieren**
4. **persistieren**
5. **Summary / Skip-Report erzeugen**

Der gemeinsame Pipeline-Baustein ist `workflows/pipeline_runner.py`.

Wichtige Regel:
- Der Pipeline-Runner kennt keine konkreten Parser oder Stores.
- Diese werden durch den jeweiligen Händler-Workflow injiziert.

### Öffentliche Pipeline-Schnittstellen

Der Pipeline-Runner arbeitet bewusst nur mit injizierten Funktionen und Ports:

- `parse_receipts(raw_records, parse_record, ...)`
- `validate_receipts(parsed_records, validate_receipt, validation_error_types, ...)`
- `persist_valid_receipts(receipts, retailer, store, ...)`

Damit bleibt die Datei ein gemeinsamer Workflow-Baustein und kein weiterer Adapter-Hub.

### Geteilte Pipeline-Metadaten

`StageResult` transportiert neben `records` und `issues` auch `total_items`.

Diese Zahl entsteht dort, wo die Pipeline die Daten wirklich kennt:

- beim Parsen als Summe der erkannten Artikel
- beim Validieren als Summe der tatsächlich gültigen Artikel

Die Händler-Workflows übernehmen diese Metadaten direkt für ihre Summaries.
Dadurch kommen LIDL- und REWE-Statistiken aus derselben gemeinsamen Quelle statt aus retailer-spezifischen Nebenpfaden.

Zusätzlich wird die workflow-nahe Fehlerabbildung jetzt über gemeinsame interne Helper vereinheitlicht.
Ziel dabei ist:
- gleiche Reason-Strings für gleiche Fehlerklassen
- konsistente Erzeugung von `ReceiptIssue`
- konsistente Erzeugung von `ReceiptParseResult` bei Einzelbon-Prüfungen

Die dafür genutzten Helper liegen in `workflows/error_mapping.py` und kapseln bewusst nur Workflow-Darstellung, nicht Parsing- oder Validatorlogik.

### Gemeinsamer Store-Port und Backend-Umschaltpunkt

Persistenz und bestehende Receipt-Snapshots laufen jetzt über denselben Store-Port:

- `shared.ports.ReceiptStore`

Der konkrete Store wird derzeit über eine kleine Factory in `storage/__init__.py` aufgelöst; das JSON-Backend liegt in `storage/json_receipt_store.py`.
Der aktuelle Umschaltpunkt liegt im CLI-Entry-Point `get_data.py` über `--write-backend` und wird in die öffentlichen Workflow-Einstiege weitergereicht.
So bleiben die internen Pipelines port-basiert, obwohl aktuell nur das JSON-Backend existiert.

## LIDL

### Öffentliche LIDL-API

- `run_lidl_check(...)`
- `run_lidl_initial(...)`
- `run_lidl_update(...)`
- `fetch_lidl_receipt_parse_result(...)`

Nicht öffentlich ist dagegen die Receipt-ID-Sammlung. Sie bleibt als `_collect_lidl_receipt_ids(...)` ein interner Orchestrierungshelfer des LIDL-Workflows.

### `run_lidl_initial(...)`
Ablauf:
1. Session vorbereiten und prüfen
2. alle Receipt-IDs sammeln
3. bekannte IDs über den konfigurierten Store laden
4. nur neue IDs bestimmen
5. gemeinsame LIDL-Pipeline ausführen
6. Skip-Report + Summary + Abschlussausgabe

### `run_lidl_update(...)`
Ablauf:
1. Session vorbereiten und prüfen
2. nur die ersten relevanten Seiten abrufen
3. bekannte IDs über den konfigurierten Store laden
4. nur neue IDs bestimmen
5. gemeinsame LIDL-Pipeline ausführen
6. Skip-Report + Summary + Abschlussausgabe

### `_run_lidl_receipt_pipeline(...)`
Verantwortung:
- Rohbons abrufen
- Parsing und Validierung mit LIDL-spezifischen Funktionen injizieren
- Persistenz über den konfigurierten `ReceiptStore`
- `WorkflowResult` aufbauen

### Verständnishilfe
Die wichtigsten LIDL-Helfer sind jetzt getrennt nach:
- Session-Aufbau: `_setup_lidl_session(...)`
- Session-Test: `_test_lidl_workflow_session(...)`
- Session-Readiness für Use Cases: `_prepare_lidl_session(...)`
- Receipt-Auswahl: `_collect_lidl_receipt_ids(...)`, `_filter_new_receipt_ids(...)`
- Pipeline-Ausgabe: `_print_lidl_pipeline_result(...)`
- Abschlussausgabe: `_print_lidl_completion(...)`

## REWE

### Öffentliche REWE-API

- `run_rewe_check(...)`
- `run_rewe_initial(...)`
- `run_rewe_update(...)`
- `import_rewe_receipts_from_pdfs(...)`
- `parse_rewe_receipt_pdf_with_result(...)`

### `run_rewe_initial(...)`
Ablauf:
1. REWE-Session laden
2. Customer-ID bestimmen
3. Session testen
4. ZIP herunterladen
5. PDFs entpacken
6. gemeinsame PDF-Importpipeline ausführen
7. Summary ausgeben

Wichtige Helfer:
- `_prepare_rewe_import_context(...)`
- `_download_and_extract_rewe_zip(...)`

### `run_rewe_update(...)`
Ablauf:
1. vorhandene lokale PDFs lesen
2. gemeinsame PDF-Importpipeline für alle gefundenen PDFs ausführen
3. Persistenz per Upsert dem konfigurierten Store überlassen
4. Summary ausgeben

### `_run_rewe_pdf_import_pipeline(...)`
Verantwortung:
- gemeinsame REWE-PDF-Importorchestrierung
- unterscheidet drei Fälle:
  1. keine PDFs vorhanden
  2. nur bereits vorab gelieferte Issues ohne verbleibende PDFs
  3. echter Parse-/Validate-/Persist-Import

Hilfsfunktionen dafür:
- `_build_rewe_missing_pdfs_result(...)`
- `_build_rewe_prefilter_only_result(...)`

### `parse_rewe_receipt_pdf_with_result(...)`
Verantwortung:
- Workflow-seitiges Parse-/Validate-Ergebnis für einen einzelnen REWE-PDF-Bon
- geeignet für Diagnostik-nahe Einzelprüfungen ohne separates Diagnostics-Paket
- kapselt Parse- und Validierungsfehler direkt in ein `ReceiptParseResult`

## Warum die Workflows trotzdem noch komplex wirken

Die Workflows sind fachlich komplex, weil sie mehrere Ebenen gleichzeitig koordinieren:
- Authentifizierung
- Remote-/Lokalquellen
- Delta-Logik
- Fortschrittsanzeigen
- Fehlerabbildung
- Reporting
- Persistenz

Das Ziel ist daher nicht "extrem kleine Dateien um jeden Preis", sondern:
- klare Unterteilung der Verantwortungen innerhalb einer Workflow-Datei
- kleine, benannte Hilfsfunktionen für wiederkehrende Teilabläufe
- injizierbare gemeinsame Pipeline-Bausteine
- dokumentierte Paketgrenzen

## Einheitliche Dateistruktur in `workflows/*`

Die Workflow-Dateien folgen jetzt möglichst derselben internen Reihenfolge:

1. **Public use cases**
2. **Public diagnostics / import helpers**
3. **Session / setup helpers**
4. **Pipeline assembly helpers**
5. **Single-receipt / selection / delta / utility helpers**

Ziel ist nicht formale Perfektion, sondern schnellere Orientierung beim Lesen.
Neue Helfer sollten deshalb möglichst in den passenden Abschnitt einsortiert werden.
Faustregel: nur Funktionen ohne führenden Unterstrich gehören zur dokumentierten Workflow-API.

## Praktische Lesereihenfolge

Für neue Entwickler ist diese Reihenfolge am hilfreichsten:

1. `docs/architecture/package-layer-rules.md`
2. dieses Dokument
3. `workflows/pipeline_runner.py`
4. `workflows/lidl_workflow.py`
5. `workflows/rewe_workflow.py`

## Nächste sinnvolle Refactoring-Kandidaten

Falls die Workflows weiter vereinfacht werden sollen, sind die nächsten Kandidaten:

1. LIDL- und REWE-Fehlerabbildung stärker vereinheitlichen
2. gemeinsame Progress-/Stage-Muster zwischen LIDL und REWE weiter angleichen
3. bei Bedarf einen eigenen `workflows/helpers/`-Bereich nur für gemeinsam genutzte Orchestrierungs-Helfer prüfen

