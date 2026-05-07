# ADR 0002: Neutrale Shared-Schicht für Receipt- und Adress-Normalisierung

- **Status:** Angenommen
- **Datum:** 2026-05-10
- **Entscheider:** Projektmaintainer
- **Bezug:** `shared/receipt_schema.py`, `shared/addresses.py`, `storage/json_receipt_store.py`, `parsing/address_extractor.py`, `receipt_schema.py`, `parsing/receipt_schema.py`

## Kontext

Im aktuellen Stand war die Receipt-Normalisierung fachlich sinnvoll, architektonisch aber falsch geschichtet:

- `storage/json_receipt_store.py` normalisiert persistierte Bons vor dem Merge.
- Dafür importierte das Repository `normalize_receipt_schema(...)` aus `receipt_schema.py`.
- Dieses Modul hing wiederum an `parsing/address_extractor.py`.

Damit entstand eine unerwünschte Abhängigkeitsrichtung:

`storage -> receipt_schema -> parsing`

Das verletzt die gewünschte Architekturregel des Projekts:

- Domänennahe, neutrale Datenstrukturen dürfen von mehreren Schichten genutzt werden.
- Parsing-spezifische Module dürfen jedoch **keine Vorbedingung** für Storage sein.
- Nur `workflows` sollen modulübergreifend orchestrieren.

Zusätzlich waren zwei unterschiedliche Verantwortungen vermischt:

1. **Parsing-nahe Extraktion** von Adressen aus Text-/HTML-Linien
2. **neutrale Schema-Normalisierung** für bereits vorliegende Receipt-/Adress-Dictionaries

## Entscheidung

Wir führen eine explizite **Shared-Schicht** für neutrale Normalisierung ein.

### Neue Zielstruktur

- `shared/addresses.py`
  - enthält nur neutrale Adress-Schema-Helfer:
    - `empty_address(...)`
    - `normalize_address(...)`
- `shared/receipt_schema.py`
  - enthält nur neutrale Receipt-Schema-Helfer:
    - `build_receipt_schema(...)`
    - `build_receipt_item(...)`
    - `normalize_receipt_schema(...)`

### Schichtungsregel

- `storage/*` darf `shared/*` importieren.
- `parsing/*` darf `shared/*` importieren.
- `shared/*` importiert **weder** `parsing`, **noch** `storage`, **noch** `workflows`.

Damit wird die Abhängigkeitsrichtung bereinigt zu:

- `storage -> shared`
- `parsing -> shared`
- `workflows -> parsing/storage/auth/api/reporting/shared`

## Umsetzung

### 1. Storage direkt auf Shared

`storage/json_receipt_store.py` importiert `normalize_receipt_schema(...)` jetzt direkt aus `shared.receipt_schema`.

Das Repository bleibt damit zuständig für:

- Laden bestehender Rohdaten
- Normalisieren vor Vergleich/Merge
- Upsert-Logik
- Sortieren
- Persistieren

Es hängt aber nicht mehr an Parsing-Modulen.

### 2. Neutrale Adress-Helfer aus Parsing herausgezogen

`empty_address(...)` und `normalize_address(...)` wurden aus der Parsing-Nähe herausgelöst und nach `shared/addresses.py` verschoben.

`parsing/address_extractor.py` bleibt zuständig für:

- Text-/Zeilen-basierte Adress-Erkennung
- Regex-Parsing von Adressmustern

Es nutzt dafür die neutralen Shared-Helfer, orchestriert aber nichts.

### 3. Kompatibilitäts-Wrapper bleiben vorerst bestehen

Zur migrationsfreundlichen Stabilisierung bleiben bestehen:

- `receipt_schema.py`
- `parsing/receipt_schema.py`

Beide sind jetzt nur noch dünne Wrapper auf `shared.receipt_schema`.

Das erlaubt:

- bestehende Imports vorerst weiter zu nutzen
- schrittweise Migration ohne Big-Bang
- geringe Änderungsbreite bei Tests und angrenzenden Modulen

## Erwogene Optionen

### Option A: Status quo beibehalten

**Beschreibung**
- `storage` importiert weiter das bisherige Schema-Modul.
- Das Schema-Modul importiert weiter Parsing-Helfer.

**Vorteile**
- kein Umbau

**Nachteile**
- falsche Schichtungsrichtung bleibt bestehen
- Storage hängt indirekt von Parsing ab
- Clean-Code-/SRP-Ziel wird verfehlt

**Entscheidung**
- Verworfen.

### Option B: Normalisierung komplett in `storage` verschieben

**Beschreibung**
- Repository oder Storage-Schicht übernimmt Schema-/Adress-Normalisierung selbst.

**Vorteile**
- Storage wäre autark

**Nachteile**
- Normalisierung ist keine Storage-spezifische Verantwortung
- Parsing würde dieselbe Logik erneut benötigen
- hohe Gefahr doppelter Wahrheitsquellen

**Entscheidung**
- Verworfen.

### Option C: Neutrales Shared-Modul für domänennahe Normalisierung

**Beschreibung**
- gemeinsame, orchestrierungsfreie Normalisierung in `shared/*`
- Parsing und Storage konsumieren dieselbe Logik

**Vorteile**
- saubere Abhängigkeitsrichtung
- eine einzige fachliche Wahrheitsquelle
- SRP-konform: Extraktion und Normalisierung getrennt
- geringe Migrationskosten durch Wrapper

**Nachteile**
- zusätzliche Modulschicht
- temporär zwei Importpfade während der Migration

**Entscheidung**
- Angenommen.

## Konsequenzen

### Positive Konsequenzen

- `storage` ist nicht mehr indirekt von `parsing` abhängig.
- Shared-Normalisierung kann von mehreren Schichten genutzt werden, ohne Orchestrierungslogik einzuführen.
- Adress-Erkennung und Adress-Normalisierung sind klarer getrennt.
- Die Architekturregel „nur Workflows orchestrieren“ wird weiter gestärkt.

### Negative Konsequenzen

- Es existieren vorübergehend Wrapper-Module für Kompatibilität.
- Entwickler müssen künftig bewusster unterscheiden zwischen:
  - Extraktion (`parsing/*`)
  - Normalisierung (`shared/*`)

## Migrationsregeln

1. **Neue direkte Importe** sollen bevorzugt auf `shared.receipt_schema` und `shared.addresses` zeigen.
2. `receipt_schema.py` und `parsing/receipt_schema.py` gelten als **Kompatibilitäts-Wrapper**, nicht als langfristige Ziel-API.
3. Parsing-Module dürfen Shared-Helfer verwenden, aber keine Storage- oder Workflow-Logik importieren.
4. Weitere neutrale fachliche Hilfslogik soll künftig zuerst auf Eignung für `shared/*` geprüft werden.

## Akzeptanzkriterien

Die Entscheidung gilt als erfolgreich umgesetzt, wenn:

1. `storage/json_receipt_store.py` keine Parsing-Module mehr direkt oder indirekt benötigt.
2. bestehende Receipt-Normalisierung unverändert funktioniert.
3. bestehende Importpfade über Wrapper vorerst kompatibel bleiben.
4. Repository-Merge, Datumssortierung und Händler-Defaults automatisiert getestet sind.

## Einschätzung für weitere Schritte

Ein Shared-Modul ist für solche Fälle die richtige Richtung, **wenn** die enthaltene Logik folgende Eigenschaften hat:

- fachlich neutral
- orchestrierungsfrei
- von mehreren Schichten wiederverwendbar
- unabhängig von I/O, Terminalausgaben und HTTP

Dazu passen insbesondere:

- Schema-Normalisierung
- Wert-/Datums-/Mengen-Normalisierung
- neutrale Identifier-/Datentyp-Helfer
- kanonische leere Strukturen wie `empty_address()`

Nicht in `shared/*` gehören dagegen:

- HTML-/PDF-/Regex-Extraktion aus konkreten Datenquellen
- Dateizugriff
- API-Requests
- Reporting/CLI-Ausgaben
- Workflow-Steuerung

Kurz: **Ja, ein `shared`-Modul ist hier die richtige Abstraktion** — aber nur für neutrale Domänenbausteine, nicht als neue Sammelstelle für beliebige Utilities.

