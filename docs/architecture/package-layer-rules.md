# Paket- und Schichtenregeln

Stand: 2026-05-10

Siehe ergänzend: `docs/architecture/workflow-overview.md`

## Zielbild

Das Projekt folgt einer einfachen, expliziten Schichtung:

1. **Entry Points**
   - `get_data.py`
   - `dashboard.py`
   - `cli/*`
2. **Workflows / Use Cases**
   - `workflows/*`
3. **Adapter**
   - `api/*`
   - `auth/*`
   - `parsing/*`
   - `storage/*`
   - `reporting/*`
4. **Neutrale Shared-Kernbausteine**
   - `shared/*`
   - `result_types.py`
   - `config/*`

## Verantwortungen pro Paket

### Entry Points (`get_data.py`, `dashboard.py`, `cli/*`)
- starten nur öffentliche Use Cases oder Menüs
- enthalten Argument-/Menü-Verkabelung, aber keine fachliche Parsing-/Persistenzlogik
- verwenden wenige explizite öffentliche Einstiege (`main()`, Menüfunktionen)
- interne Routing-, Dispatch- und Prompt-Helfer bleiben privat und beginnen mit `_`
- konfigurieren technische Umschaltpunkte wie das aktuell ausgewählte Write-Backend und reichen diese in die Workflow-Einstiege weiter

### `api/*`
- nur HTTP-/Transportlogik
- keine Auth-Orchestrierung
- kein Reporting
- keine Workflow-Steuerung

### `auth/*`
- nur Auth-Quellen, Session-Erzeugung, kundennahe Auth-Helfer
- keine fachliche Abruf-Orchestrierung
- keine Reporting-Ausgaben

### `parsing/*`
- nur Extraktion, Ableitung und Normalisierung aus HTML/PDF/Text
- keine Persistenz
- keine Workflow-Steuerung
- keine CLI-/Reporting-Ausgaben

### `storage/*`
- nur Persistenz und Dateizugriff
- keine Parsing-Logik
- keine Workflow-Steuerung

### `reporting/*`
- nur Ausgabe, Formatierung, Report-Dateien
- keine API-/Auth-/Parsing-/Storage-Orchestrierung

### `workflows/*`
- einzige Orchestrierungsschicht
- kombiniert Adapter, Shared-Bausteine und Ergebnisobjekte zu Use Cases
- kennt Abläufe, aber möglichst keine technischen Details innerhalb der Adapter
- kleine Hilfsfunktionen bleiben lokal in dem Workflow-Baustein, der sie wirklich benötigt
- Pipeline-Metadaten wie aggregierte Artikelzahlen gehören in gemeinsame Pipeline-Bausteine, nicht in retailer-spezifische Helper-Dateien
- öffentliche Workflow-APIs bestehen nur aus expliziten, underscore-freien Einstiegspunkten (z. B. Use Cases oder bewusst freigegebenen Diagnose-Helfern)
- interne Assembly-, Delta-, Session- und Utility-Helfer bleiben privat und beginnen mit `_`

### `shared/*`
- nur neutrale, orchestrierungsfreie Domänenbausteine
- keine Adapter- oder Workflow-Abhängigkeiten
- geeignet für Schema-, Adress-, Wert- und Port-Definitionen

## Zulässige Abhängigkeitsrichtungen

- `entry points -> workflows`
- `workflows -> api|auth|parsing|storage|reporting|shared|result_types|config`
- `api -> config`
- `auth -> config`
- `parsing -> shared`
- `storage -> shared|config|result_types`
- `reporting -> config|result_types`
- `shared -> result_types|shared`

## Nicht zulässig

- `api|auth|parsing|storage|reporting -> workflows`
- `storage -> parsing`
- `parsing -> storage`
- `reporting -> workflows`
- `shared -> api|auth|parsing|storage|reporting|workflows`
- Wrapper-Module als dauerhafte API-Stellvertreter

## Kanonische Importpfade

Nach ADR 0003 gelten für gemeinsam genutzte Fachbausteine nur noch die direkten Zielpfade:

| Zweck | Kanonischer Pfad |
| --- | --- |
| Receipt-Schema / Normalisierung | `shared.receipt_schema` |
| Address-Schema | `shared.addresses` |
| Persistenz-Port | `shared.ports.ReceiptStore` |
| Parse-/Workflow-Resulttypen | `result_types` |

Typische Beispiele:

- `from shared.receipt_schema import build_receipt_schema`
- `from shared.addresses import normalize_address`
- `from shared.ports import ReceiptStore`
- `from result_types import ReceiptParseResult, PersistResult, WorkflowSummary`

### Verbotene Altpfade

Folgende Importpfade gelten als entfernt und dürfen weder in Produktivcode noch in Tests neu auftauchen:

- `receipt_schema`
- `parsing.receipt_schema`
- `parsing.receipt_parse_result`
- `diagnostics.*`

Wenn vorhandener Code noch einen alten Pfad referenziert, soll er auf den kanonischen Zielpfad migriert werden statt einen neuen Wrapper einzuführen.

## Architekturregeln für neue Änderungen

1. Neue gemeinsame Fachlogik zuerst auf Eignung für `shared/*` prüfen.
2. Neue technische Integrationen in das passende Adapter-Paket legen.
3. Wenn mehrere Adapter koordiniert werden müssen, gehört das in `workflows/*`.
4. Tests sollen bevorzugt die **kanonischen** Importpfade verwenden, nicht alte Kompatibilitätsnamen.
5. Rückwärtskompatible Wrapper sind nur als kurze Migration erlaubt und danach zu entfernen.

## Review-Checkliste für Beiträge

Vor dem Mergen einer Architekturänderung kurz prüfen:

1. Importiert `workflows/*` nur konkrete Adapter dort, wo echte Orchestrierung stattfindet?
2. Bleibt `workflows/pipeline_runner.py` frei von direkten `parsing/*`- und `storage/*`-Adapterimports?
3. Verwenden neue Tests und Module ausschließlich die kanonischen Importpfade?
4. Liegt gemeinsame Fachlogik in `shared/*` oder `result_types.py` statt in retailer-spezifischen Workflows?
5. Sind neue Dokumentations- oder ADR-Verweise im Root-`readme.md` sichtbar gemacht?

