# ADR 0003: Explizite Paket-Schichtenregeln und Entfernung temporärer Wrapper

- **Status:** Angenommen
- **Datum:** 2026-05-10
- **Entscheider:** Projektmaintainer
- **Bezug:** `docs/architecture/package-layer-rules.md`, `shared/receipt_schema.py`, `shared/addresses.py`, `shared/ports.py`, `workflows/pipeline_runner.py`

## Kontext

Nach der ersten Architektur-Bereinigung waren bereits zentrale Rückwärtsabhängigkeiten entfernt worden. Es blieben jedoch zwei Restklassen von Problemen:

1. **temporäre Wrapper-Module**
   - `receipt_schema.py`
   - `parsing/receipt_schema.py`
   - `parsing/receipt_parse_result.py`
   - `diagnostics/*`
2. **indirekte Querzugriffe und Re-Export-Pfade**
   - Tests und einzelne Module nutzten noch nicht die kanonischen Importpfade
   - `workflows/pipeline_runner.py` hing weiterhin konkret an Parsing- und Storage-Adaptern
   - Port-/Typgrenzen waren noch nicht als Zielarchitektur dokumentiert

Diese Reste erzeugen langfristig mehrere Nachteile:

- unklare kanonische API-Pfade
- neue Rückwärtsabhängigkeiten werden versehentlich wieder eingeführt
- Schichtenregeln sind nur implizit bekannt
- technische Adapterkopplung bleibt in gemeinsam genutzten Workflow-Bausteinen stecken

## Entscheidung

Wir gehen auf eine **explizite Zielarchitektur ohne Wrapper** über.

### Kernaussagen

1. Temporäre Wrapper werden entfernt, sobald alle Importe auf kanonische Pfade migriert sind.
2. Kanonische Shared-Pfade für neutrale Fachbausteine sind:
   - `shared.receipt_schema`
   - `shared.addresses`
   - `shared.ports`
   - `result_types`
3. `workflows/*` bleibt die einzige Orchestrierungsschicht.
4. Gemeinsam genutzte Workflow-Bausteine wie `workflows/pipeline_runner.py` arbeiten nur noch mit injizierten Funktionen/Ports statt mit harten Adapterimporten.
5. Paket-Schichtenregeln werden explizit dokumentiert und automatisiert getestet.
6. Pipeline-nahe Aggregationen wie die Gesamtzahl der Artikel werden im Pipeline-Kontext geführt und nicht in retailer-spezifischen Hilfsmodulen ausgelagert.

## Umsetzung

### 1. Wrapper entfernt

Folgende temporären Wrapper werden vollständig entfernt:

- `receipt_schema.py`
- `parsing/receipt_schema.py`
- `parsing/receipt_parse_result.py`
- `diagnostics/__init__.py`
- `diagnostics/lidl_diagnostics.py`
- `diagnostics/rewe_diagnostics.py`

### 2. Kanonische Importpfade

Ab jetzt gelten folgende direkten Importpfade:

- Receipt-Schema: `shared.receipt_schema`
- Address-Schema: `shared.addresses`
- Parse-Result-Typ: `result_types.ReceiptParseResult`
- Persistenz-Port: `shared.ports.ReceiptStore`

### 3. Pipeline-Runner entkoppelt

`workflows/pipeline_runner.py` importiert keine konkreten Parsing- oder Storage-Adapter mehr.

Stattdessen werden übergeben:

- `parse_record(...)`
- `validate_receipt(...)`
- `validation_error_types`
- `store`

Dadurch bleibt der Pipeline-Runner ein reiner Workflow-Baustein.

### 4. Architekturregeln dokumentiert und testbar gemacht

Die Zielarchitektur ist zusätzlich in `docs/architecture/package-layer-rules.md` festgehalten.

Automatisierte Architekturtests stellen sicher, dass:

- entfernte Wrapper-Dateien nicht wieder auftauchen
- verbotene Paketimporte nicht unbemerkt eingeführt werden
- der Pipeline-Runner keine konkreten Parsing-/Storage-Adapter direkt importiert

### 5. Pipeline-Metadaten zentralisiert

Die Artikelaggregation wurde aus dem separaten Hilfsmodul `workflows/receipt_sync.py` in `workflows/pipeline_runner.py` verlagert.

Konkret bedeutet das:

- `validate_receipts(...)` führt `total_items` direkt mit
- `StageResult` transportiert diese Metadaten explizit weiter
- `lidl_workflow` und `rewe_workflow` verwenden `validation_result.total_items`
- REWE- und LIDL-Summaries basieren damit auf derselben Pipeline-Quelle

### 6. Workflow-nahe Fehlerabbildung vereinheitlicht

Wiederkehrende Fehlerabbildung für:

- `ReceiptIssue`
- `ReceiptParseResult`
- Validatorfehler-Reason-Strings

wurde in gemeinsame workflow-interne Helper ausgelagert.

Ziel ist keine fachliche Änderung, sondern:

- konsistentere Reason-Texte
- weniger doppelte String- und Objekt-Erzeugung
- besser lesbare Workflow-Dateien

## Erwogene Optionen

### Option A: Wrapper dauerhaft behalten

**Vorteile**
- kurzfristig bequem

**Nachteile**
- mehrere scheinbar gültige APIs
- neue Altpfade verbreiten sich weiter
- Architektur bleibt weich und uneindeutig

**Entscheidung**
- Verworfen.

### Option B: Wrapper entfernen, aber ohne dokumentierte Schichtenregeln

**Vorteile**
- weniger Code

**Nachteile**
- gleiche Fehler treten später erneut auf
- Architekturwissen bleibt implizit

**Entscheidung**
- Verworfen.

### Option C: Wrapper entfernen und Paketregeln explizit festziehen

**Vorteile**
- klare Zielarchitektur
- eindeutige Importpfade
- weniger Querzugriffe
- automatisiert absicherbar

**Nachteile**
- einmalige Umstellung mehrerer Tests und Imports

**Entscheidung**
- Angenommen.

## Konsequenzen

### Positiv

- klare kanonische Importpfade
- keine künstlichen Zwischen-APIs mehr
- gemeinsame Workflow-Bausteine sind sauberer von Adaptern getrennt
- Schichtenregeln sind dokumentiert und überprüfbar
- gemeinsame Aggregatlogik liegt dort, wo sie fachlich entsteht
- wiederkehrende Fehlerabbildung ist im Workflow-Kontext vereinheitlicht

### Negativ

- externe Altimporte wären jetzt brechend
- neue Beiträge müssen die Schichtenregeln bewusst einhalten

## Akzeptanzkriterien

Die Entscheidung gilt als umgesetzt, wenn:

1. keine produktiven oder testseitigen Imports mehr auf entfernte Wrapper zeigen
2. entfernte Wrapper-Dateien nicht mehr vorhanden sind
3. `workflows/pipeline_runner.py` keine direkten Parsing-/Storage-Adapter importiert
4. Architektur-Regeltests und komplette Regressionstest-Suite erfolgreich laufen

