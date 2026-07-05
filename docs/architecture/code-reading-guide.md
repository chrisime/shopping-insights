# Code-Leseguide: So findest du dich im Projekt zurecht

Stand: 2026-05-11

Dieses Dokument ist bewusst **kein Architektur-Manifest**, sondern eine praktische Lesehilfe.
Wenn dir das Projekt gerade schwer verständlich vorkommt, lies **nicht** alles paketweise von oben nach unten.
Der schnellste Einstieg ist: **einen konkreten Ablauf verfolgen**.

Siehe ergänzend:

- `docs/architecture/package-layer-rules.md`
- `docs/architecture/workflow-overview.md`

---

## 1. Das wichtigste mentale Modell

Das Projekt besteht im Kern aus **drei Ebenen**:

1. **Einstieg / Auslösen**
   - `fetch_tickets.py`
   - `cli/*`
   - `dashboard.py`

2. **Ablaufsteuerung / Use Cases**
    - `workflows/*`

3. **Bausteine, die vom Workflow benutzt werden**
   - `auth/*` → Session, Cookies, Browser-/Datei-Auth
   - `api/*` → HTTP-Aufrufe zu LIDL/REWE
   - `parsing/*` → HTML/PDF/Text in strukturierte Receipt-Daten umwandeln
   - `storage/*` → JSON/SQLite speichern und wiederfinden
   - `reporting/*` → Terminal-Ausgaben, Reports
   - `shared/*` → neutrale Hilfsbausteine und Schema-Normalisierung

4. **Frontend-/Dashboard-Schicht**
   - `frontend/*`
   - `dashboard.py`

Die wichtigste Idee ist:

> **Nur `workflows/*` darf die anderen Bausteine zu einem echten Ablauf zusammensetzen.**

Wenn du also verstehen willst, **was das System tut**, beginne fast immer bei `workflows/*`.
Wenn du verstehen willst, **wie ein Detail technisch umgesetzt ist**, springe danach in `api/*`, `parsing/*`, `storage/*` oder `auth/*`.

---

## 2. Die einfachste Landkarte des Projekts

```text
Benutzer / CLI / Menü
        |
        v
   fetch_tickets.py / cli/*
        |
        v
     workflows/*
   (echte Orchestrierung)
   /    |      |      \
  v     v      v       v
auth   api   parsing  storage
  \     |      |       /
   \    |      |      /
    \   v      v     /
       shared/*
    + result_types.py
```

Wichtig dabei:

- `shared/*` ist der neutrale Kern
- `result_types.py` enthält kleine gemeinsame Ergebnisobjekte
- `storage/*` speichert **normalisierte** Receipts, nicht Rohdaten
- `parsing/*` soll extrahieren, aber **nicht** selbst speichern
- `dashboard.py` ist derzeit eher ein **separater Auswerte-Entry-Point** und architektonisch noch nicht so sauber wie die neueren Workflow-Pfade
- `frontend/*` enthält die Zwischenebene für Streamlit und den späteren Vue-Übergang

---

## 3. Wenn du nur 30 Minuten hast: Lies in dieser Reihenfolge

### Für das Gesamtverständnis

1. `readme.md`
2. `docs/architecture/code-reading-guide.md` *(dieses Dokument)*
3. `docs/architecture/package-layer-rules.md`
4. `docs/architecture/workflow-overview.md`
5. `fetch_tickets.py`
6. `workflows/pipeline_runner.py`
7. `workflows/lidl_workflow.py`
8. `workflows/rewe_workflow.py`

### Für das Datenmodell-Verständnis

1. `shared/receipt_schema.py`
2. `retailers/receipt_schema_profiles.py`
3. `shared/addresses.py`
4. `shared/payment_methods.py`
5. `storage/json_receipt_store.py`
6. `storage/sqlite_receipt_store.py`

### Für einen konkreten Händler

**LIDL:**

1. `workflows/lidl_workflow.py`
2. `api/lidl_client.py`
3. `parsing/lidl_receipt_parser.py`
4. `parsing/lidl_validator.py`
5. `storage/*`

**REWE:**

1. `workflows/rewe_workflow.py`
2. `api/rewe_client.py`
3. `parsing/rewe_pdf_parser.py`
4. `parsing/rewe_validator.py`
5. `storage/*`

---

## 4. Der wichtigste Ablauf: Was passiert bei `python fetch_tickets.py ...`?

## 4.1 Einstieg über `fetch_tickets.py`

`fetch_tickets.py` ist der zentrale CLI-Einstieg.

Seine Aufgabe ist **nicht**, fachliche Arbeit zu erledigen, sondern nur:

- Argumente parsen
- Händler auswählen (`lidl` / `rewe`)
- Modus auswählen (`initial` / `update` / `check`)
- passenden Workflow aufrufen

Merksatz:

> `fetch_tickets.py` beantwortet die Frage: **Welcher Use Case soll laufen?**

Nicht:

> **Wie genau wird ein Bon geparst oder gespeichert?**

---

## 4.2 Danach landet man in `workflows/*`

Beispiel LIDL:

```text
fetch_tickets.py
  -> workflows.lidl_workflow.run_lidl_initial()
     -> Session vorbereiten
     -> Receipt-IDs sammeln
     -> bekannte IDs aus Store lesen
     -> neue IDs filtern
     -> Pipeline ausführen
     -> Summary / Reporting
```

Beispiel REWE:

```text
fetch_tickets.py
  -> workflows.rewe_workflow.run_rewe_initial()
     -> Session + customerId vorbereiten
     -> ZIP herunterladen
     -> PDFs entpacken
     -> PDF-Importpipeline ausführen
     -> Summary / Reporting
```

Die Workflow-Dateien sind also die Antwort auf die Frage:

> **Welche Schritte passieren in welcher Reihenfolge?**

---

## 4.3 Die gemeinsame Pipeline in `workflows/pipeline_runner.py`

`pipeline_runner.py` ist eine der wichtigsten Dateien im Projekt.
Sie enthält die gemeinsame lineare Pipeline:

1. parsen
2. validieren
3. persistieren

Wichtig ist, was diese Datei **nicht** tut:

- sie kennt keinen konkreten LIDL-Parser
- sie kennt keinen konkreten REWE-Parser
- sie kennt keinen konkreten JSON- oder SQLite-Store

Stattdessen bekommt sie Funktionen und Ports von außen übergeben.

Das heißt konkret:

- `parse_receipts(...)` bekommt `parse_record`
- `validate_receipts(...)` bekommt `validate_receipt`
- `persist_valid_receipts(...)` bekommt einen `ReceiptStore`

Das ist architektonisch sehr wichtig, weil dadurch die gemeinsame Pipeline **wiederverwendbar** bleibt.

---

## 5. Wie du `shared/receipt_schema.py` lesen solltest

Diese Datei wirkt auf den ersten Blick abstrakt, ist aber in Wahrheit sehr zentral.

Sie beantwortet die Frage:

> **Wie sieht ein normalisierter Bon im System aus?**

### 5.1 Warum die Datei existiert

LIDL und REWE liefern Daten in unterschiedlichen Formaten.
Bevor gespeichert oder verglichen wird, braucht das Projekt ein gemeinsames Zielmodell.

`shared/receipt_schema.py` sorgt dafür, dass aus uneinheitlichen Eingaben ein konsistentes Receipt-Dictionary wird.

### 5.2 Die drei wichtigsten öffentlichen Bausteine

#### `ReceiptSchemaProfile`

Ein Profil ergänzt gemeinsame Felder um händler-spezifische Extras.

Beispiel:

- LIDL hat zusätzliche Spar-Felder wie `lidlplus_amount_saved`
- REWE hat Bonus-Felder wie `rewe_bonus_amount_saved`

Die Datei selbst bleibt dadurch **neutral**, und retailer-spezifische Zusätze liegen in
`retailers/receipt_schema_profiles.py`.

#### `build_receipt_schema(...)`

Erzeugt ein neues Receipt-Dictionary mit Standardfeldern.

Typische Verantwortung:

- gemeinsame Grundstruktur anlegen
- Defaults für optionale Felder setzen
- mutable Defaults sauber kopieren (`[]`, `{}`)

#### `normalize_receipt_schema(...)`

Das ist die wichtigste Funktion in der Datei.

Sie nimmt bestehende Receipt-Daten und macht sie konsistent:

- Retailer sicher auflösen
- Basisstruktur ergänzen
- Metadaten normieren
- Adressen normieren
- Geldwerte in `float` umwandeln
- `items` und `payment_methods` säubern

Praktisch ist das die Funktion:

> **"Mach aus beliebigen Receipt-Daten das Projekt-Zielformat."**

### 5.3 Warum das für die Architektur wichtig ist

Die Datei ist ein gutes Beispiel für `shared/*`:

- keine API-Aufrufe
- keine Dateizugriffe
- keine Workflow-Steuerung
- keine Händler-Orchestrierung

Sondern nur:

- neutrale Datenform
- Normalisierung
- kleine Wertkonvertierung

Genau deshalb ist sie ein guter Ort für gemeinsame Fachlogik.

---

## 6. Wie `ReceiptSchemaProfile` und Retailer-Profile zusammenhängen

Die Rollen sind getrennt:

### In `shared/receipt_schema.py`

- allgemeine Definition, **wie** Profile aussehen
- allgemeine Normalisierungslogik

### In `retailers/receipt_schema_profiles.py`

- konkrete Händler-Erweiterungen, **welche** Extra-Felder es gibt

Beispiel:

```text
shared.receipt_schema
    definiert: ReceiptSchemaProfile
        ^
        |
retailers.receipt_schema_profiles
    erstellt: Profile für lidl und rewe
        |
        v
storage/* nutzt diese Profile bei der Normalisierung
```

Das ist eine saubere Trennung, weil `shared/*` nicht wissen muss, welche Händler es konkret gibt.

---

## 7. Die kleinsten, aber wichtigsten Architektur-Bausteine

Wenn du das Projekt besser verstehen willst, achte auf diese Typen:

### `shared.ports.ReceiptStore`

Das ist der Persistenzvertrag zwischen Workflow und Storage.

Der Workflow weiß dadurch nur:

- ich kann vorhandene IDs abfragen
- ich kann Receipts persistieren

Der Workflow weiß **nicht**, ob darunter JSON oder SQLite benutzt wird.

Das ist der wichtigste Entkopplungspunkt zwischen `workflows/*` und `storage/*`.

### `result_types.PersistResult`

Kleines neutrales Ergebnis einer Speicheroperation.

### `result_types.WorkflowSummary`

Gemeinsame Zusammenfassung eines kompletten Workflows.

### `workflows.pipeline_types.RawReceiptRecord`

Rohdatensatz mit `source_id` + unbearbeiteter Payload.

### `workflows.pipeline_types.ParsedReceiptRecord`

Parsiertes Ergebnis nach der Parse-Stufe.

### `workflows.pipeline_types.ReceiptIssue`

Einheitliche Repräsentation von Problemen/Skips in der Workflow-Schicht.

Diese kleinen Typen machen den Code oft verständlicher als lange lose Dict-Ketten.

---

## 8. LIDL-Ende-zu-Ende: Welche Datei ist wofür zuständig?

```text
fetch_tickets.py
  -> workflows/lidl_workflow.py
       -> auth/session_manager.py
       -> api/lidl_client.py
       -> parsing/lidl_receipt_parser.py
       -> parsing/lidl_validator.py
       -> storage/*
       -> reporting/*
```

Praktische Leselogik:

### `workflows/lidl_workflow.py`

Hier verstehst du zuerst die Reihenfolge:

- Session vorbereiten
- Session testen
- Receipt-IDs sammeln
- neue IDs bestimmen
- Pipeline ausführen
- Reporting/Abschluss

### `api/lidl_client.py`

Hier siehst du die eigentlichen Remote-Aufrufe:

- Ticketlisten
- Ticketdetails
- Session-Test

### `parsing/lidl_receipt_parser.py`

Hier wird aus dem HTML bzw. Rohformat ein normalisiertes Receipt-Dictionary.

### `parsing/lidl_validator.py`

Hier wird geprüft, ob das Ergebnis plausibel und vollständig genug ist.

### `storage/*`

Hier wird das normalisierte Ergebnis gespeichert.

---

## 9. REWE-Ende-zu-Ende: Welche Datei ist wofür zuständig?

```text
fetch_tickets.py
  -> workflows/rewe_workflow.py
       -> auth/session_manager.py
       -> auth/rewe_customer_id.py
       -> api/rewe_client.py
       -> parsing/rewe_pdf_parser.py
       -> parsing/rewe_validator.py
       -> storage/*
       -> reporting/*
```

Wichtiger Unterschied zu LIDL:

- LIDL arbeitet stärker API-/HTML-basiert
- REWE arbeitet stark über ZIP + extrahierte PDFs

Trotzdem laufen beide am Ende in dieselbe Grundidee:

> Rohdaten → Parsing → Validierung → Persistenz → Summary

Genau deshalb ist die gemeinsame Pipeline sinnvoll.

---

## 10. Wo die Architektur schon klar ist – und wo noch Reibung steckt

Für das Verständnis sehr wichtig: Das Projekt ist **nicht überall gleich modernisiert**.

### Relativ klar und konsistent

- `workflows/*`
- `shared/*`
- `result_types.py`
- `shared.ports.ReceiptStore`
- die Trennung zwischen Parsern, Validatoren und Stores

### Noch etwas schwerer / historisch gewachsen

- `dashboard.py`
  - enthält noch recht viel Datenlogik direkt im Entry Point
  - ist damit architektonisch weniger sauber als die Import-Workflows
- parallele Unterstützung von `json` und `sqlite`
  - nützlich, aber erhöht die mentale Last
- retailer-spezifische Spezialfelder
  - fachlich sinnvoll, aber im Datenmodell nicht sofort selbsterklärend

Das ist wichtig, weil du sonst schnell denkst:

> "Ich verstehe die Architektur nicht."

Oft ist die ehrlichere Aussage:

> "Ein Teil ist schon sauber geschichtet, ein anderer Teil ist noch Übergangs-/Legacy-nah."

Das ist ein großer Unterschied.

---

## 11. Praktische Heuristik beim Lesen einzelner Dateien

Wenn du eine Datei öffnest, frage immer zuerst:

1. **Ist das ein Entry Point, ein Workflow, ein Adapter oder Shared-Code?**
2. **Darf diese Datei eigentlich orchestrieren?**
3. **Arbeitet sie auf Rohdaten oder auf normalisierten Receipts?**
4. **Gibt sie nur etwas aus / speichert etwas / oder trifft sie fachliche Entscheidungen?**

Damit werden viele Dateien sofort verständlicher.

Beispiele:

- `workflows/lidl_workflow.py` → darf orchestrieren
- `parsing/rewe_pdf_parser.py` → soll extrahieren, aber nicht speichern
- `storage/json_receipt_store.py` → soll speichern, aber nicht parsen
- `shared/receipt_schema.py` → soll nur normalisieren, nicht orchestrieren

---

## 12. Wenn du einen Bug oder Feature-Wunsch nachverfolgen willst

Nutze diese Startpunkte:

### „Import klappt nicht“

1. `fetch_tickets.py`
2. passender Workflow in `workflows/*`
3. `auth/*` oder `api/*`
4. `reporting/*` für sichtbare Fehlermeldungen

### „Ein Feld im Receipt ist falsch“

1. `parsing/*`
2. `shared/receipt_schema.py`
3. `retailers/receipt_schema_profiles.py`
4. `storage/*`

### „Ein Receipt wird zu Unrecht verworfen“

1. `workflows/error_mapping.py`
2. `parsing/*_validator.py`
3. `workflows/pipeline_runner.py`

### „JSON/SQLite speichert anders als erwartet“

1. `shared.ports.py`
2. `storage/__init__.py`
3. `storage/json_receipt_store.py`
4. `storage/sqlite_receipt_store.py`

---

## 13. Konkrete Lesestrategie für dich

Wenn du das Projekt wirklich verstehen möchtest, würde ich **nicht** mit allen Dateien anfangen, sondern mit genau diesem Pfad:

### Runde 1: Nur Ablauf verstehen

- `fetch_tickets.py`
- `workflows/pipeline_runner.py`
- `workflows/lidl_workflow.py`
- `workflows/rewe_workflow.py`

Ziel: nur verstehen, **wer wen aufruft**.

### Runde 2: Nur Datenmodell verstehen

- `shared/receipt_schema.py`
- `retailers/receipt_schema_profiles.py`
- `shared/addresses.py`
- `shared/ports.py`
- `result_types.py`

Ziel: verstehen, **wie ein Receipt im System aussieht**.

### Runde 3: Erst dann technische Details

- `api/*`
- `auth/*`
- `parsing/*`
- `storage/*`

Ziel: verstehen, **wie die Arbeit innerhalb der Bausteine passiert**.

---

## 14. Kurzfassung in einem Satz pro Hauptpaket

- `fetch_tickets.py` → startet den passenden Use Case
- `cli/*` → interaktive Benutzerführung
- `workflows/*` → steuert komplette Abläufe
- `auth/*` → baut Sessions und liest Auth-Quellen
- `api/*` → spricht mit externen Endpunkten
- `parsing/*` → macht aus Rohdaten strukturierte Receipts
- `storage/*` → speichert normalisierte Receipts
- `reporting/*` → macht Terminal-/Report-Ausgabe
- `shared/*` → neutraler Kern ohne Orchestrierung
- `retailers/*` → retailer-spezifische Profile/Registries außerhalb des neutralen Kerns
- `result_types.py` → kleine gemeinsame Ergebnisobjekte

---

## 15. Wichtigster Take-away

Wenn du beim Lesen unsicher bist, nimm diese Faustregel:

> **Will ich den Ablauf verstehen? → `workflows/*`**
>
> **Will ich die Datenform verstehen? → `shared/receipt_schema.py`**
>
> **Will ich die Technik eines Schritts verstehen? → das passende Adapter-Paket**

Wenn du magst, ist der nächste sinnvolle Schritt eine zweite, noch praktischere Hilfe:

- ein **konkreter Call-Flow für LIDL** mit Datei-für-Datei-Sprungliste
- ein **konkreter Call-Flow für REWE**
- oder ein **Kommentar-/Refactoring-Durchgang** für besonders schwere Dateien wie `workflows/lidl_workflow.py` oder `shared/receipt_schema.py`
