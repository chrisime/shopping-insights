# Workflow-Überblick

Stand: 2026-05-21

Dieses Dokument beschreibt die fachlichen Hauptabläufe in `workflows/*` in einer kompakteren Form als Einstieg für Wartung und Refactoring.

## Grundidee

`workflows/*` ist die einzige Orchestrierungsschicht.

Öffentlich gemacht werden dort nur echte Einstiegspunkte:

- Use Cases wie `run_lidl_initial(...)`, `run_rewe_initial(...)` oder `run_rewe_update(...)`

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

### Oeffentliche Pipeline-Schnittstellen

Der Pipeline-Runner arbeitet bewusst nur mit injizierten Funktionen und Ports:

- `parse_receipts(raw_records, retailer, ...)`
- `validate_receipts(parsed_records, retailer, ...)`
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

### Gemeinsamer Store-Port und Persistenzmodell

Persistenz und bestehende Receipt-Snapshots laufen ueber denselben Store-Port:

- `shared.receipt_store.ReceiptStore`

Der konkrete Persistenz-Store wird ueber `storage/__init__.py` aufgeloest und schreibt standardmaessig nach `shopping_receipts.sqlite` (DB-first).
Externe Formate werden nicht mehr als Write-Backend ausgewaehlt, sondern ueber Export-Adapter erzeugt (aktuell JSON ueber `export/json_export.py`).

## LIDL

### Oeffentliche LIDL-API

- `run_lidl_initial(...)`
- `run_lidl_update(...)`

Nicht oeffentlich sind die internen Session-/Collection-/Pipeline-Helper.

### `run_lidl_initial(...)`
Ablauf:
1. Session vorbereiten und prüfen
2. alle Ticket-Seiten der LIDL-API sammeln
3. bestehende Receipt-IDs aus dem Store laden
4. nur neue Receipts ueber stabile `receipt_id` bestimmen
5. Ticket-JSONs herunterladen und lokal speichern
6. gemeinsame LIDL-Pipeline ausführen
7. Skip-Report + Summary + Abschlussausgabe

### `run_lidl_update(...)`
Ablauf:
1. keine API-Abfrage – vorhandene lokale JSONs per Upsert reimportieren
2. gemeinsame LIDL-Pipeline ausführen
3. Skip-Report + Summary + Abschlussausgabe

### Gemeinsame `DownloadImportWorkflow`-Superklasse

Beide LIDL-Workflows (`run_lidl_initial`, `run_lidl_update`) delegieren an
`_LidlDownloadImportWorkflow`, das von `DownloadImportWorkflow` (ABC in
`workflows/download_import_workflow.py`) erbt.

Das ABC stellt zwei Template-Methoden bereit:

- `run_initial(output_dir, store)` – Download → Import → Summary
- `run_update(output_dir, store)` – Kein-Download-Info → Vorbedingungsprüfung → Import → Summary

Abstrakte Schritte, die Unterklassen implementieren müssen:

- `_download_sources(output_dir, store) → bool`
- `_run_local_import(output_dir, store) → WorkflowResult`
- `_print_import_summary(result)`
- `_print_no_download_info()`

Optionale Hooks (default: no-op):

- `_validate_update_preconditions(output_dir) → bool`
- `_post_import(result, output_dir)`

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
- Receipt-Auswahl: `_collect_lidl_receipt_sources(...)`, `_filter_lidl_receipt_ids_for_processing(...)`
- Pipeline-Ausgabe: `_print_lidl_pipeline_result(...)`
- Abschlussausgabe: `_print_lidl_completion(...)`

## REWE

### Oeffentliche REWE-API

- `run_rewe_initial(...)`
- `run_rewe_update(...)`

### `run_rewe_initial(...)`
Ablauf:
1. REWE-Session laden
2. Customer-ID bestimmen
3. Session testen
4. ZIP herunterladen
5. PDFs entpacken
6. gemeinsame PDF-Importpipeline ausführen
7. Summary ausgeben
8. Customer-ID cachen (Post-Import-Hook)

Delegiert intern an `_ReweDownloadImportWorkflow(DownloadImportWorkflow)`.

### `run_rewe_update(...)`
Ablauf:
1. vorhandene lokale PDFs lesen
2. gemeinsame PDF-Importpipeline für alle gefundenen PDFs ausführen
3. Persistenz per Upsert dem DB-Store ueberlassen
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

### Export-Workflow

Fuer Ausgabeformate aus dem aktuellen DB-Stand gibt es einen separaten Workflow:

- `workflows/export_workflow.py` mit `run_export_json_from_db(...)`

Dieser Pfad liest aus SQLite und erzeugt aktuell JSON-Dateien ueber `export/json_export.py`.

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

## Einheitliches Import-Summary-Format

`reporting/shared_reporting.py` stellt zwei retailer-unabhängige Helfer bereit:

- `write_skipped_receipts_report(skipped_details, report_path)` – schreibt den Skip-Report
- `print_import_summary(summary, label)` – druckt die Zusammenfassung im einheitlichen Format:

```
✓ <label>: X neu/aktualisiert, Y übersprungen, Z Artikel, N insgesamt in FILE
```

Beide LIDL- und REWE-Reporting-Module delegieren an diese gemeinsamen Funktionen.
Die händlerspezifischen Wrapper (`print_lidl_import_summary`, `print_rewe_import_summary`) bleiben erhalten,
aber ihr Ausgabeformat ist jetzt identisch.

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

