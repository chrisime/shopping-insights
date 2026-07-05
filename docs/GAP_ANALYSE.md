# Gap-Analyse: Zusammenführung `shopping-analyzer` (Lidl) + `rewe-ebon-analyse` (REWE)

> Erstellt: Mai 2026  
> Ziel: Vollständige Bestandsaufnahme, welche Features 1:1 übernommen werden können, welche Anpassung/Harmonisierung erfordern und was neu gebaut werden muss.

---

## 1. Legende

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | 1:1 übertragbar / kein Anpassungsaufwand |
| 🔧 | Erfordert moderate Anpassung / Harmonisierung |
| 🏗️ | Muss neu gebaut werden |
| ⚠️ | Offener Klärungsbedarf / Designentscheidung nötig |
| ❌ | Im anderen Projekt nicht vorhanden |

---

## 2. Übersicht – Funktionale Bereiche

| Bereich | Lidl (`shopping-analyzer`) | REWE (`rewe-ebon-analyse`) | Handlungsbedarf |
|---------|---------------------------|---------------------------|-----------------|
| Datenimport | API + Browser-Cookies | EML/PDF aus lokalem Ordner | 🏗️ Superstore-Adapter nötig |
| Authentifizierung | Firefox/Chrome/Cookie-Datei | Keine (lokal) | 🔧 Nur für Lidl relevant, kapseln |
| Parsing | HTML-Receipt-Parser | PDF-Textparser (Regex) | 🔧 Gemeinsames Zwischenformat definieren |
| Persistenz | JSON-Datei | SQLite | ⚠️ Architekturentscheidung: SQLite empfohlen |
| Inkrementelle Updates | ID-basiert (JSON) | `processed_files`-Tabelle (SQLite) | 🔧 Vereinheitlichen |
| Kategorisierung | ❌ Keine | ✅ Keyword-Mapping (15 Kategorien) | 🔧 Keyword-Listen ggf. um Lidl-Artikelnamen erweitern |
| Artikel-Gruppen | ❌ Keine | ✅ `groups.json` + lokaler Save-Server | ✅ 1:1 übernehmen, Superstore-neutral |
| Dashboard | Streamlit (Python) | Statisches HTML+Chart.js | ⚠️ Architekturentscheidung: eines wählen oder beide anbieten |
| Analyse – Grundkennzahlen | ✅ Streamlit-KPIs | ✅ HTML-Statistiken | 🔧 Zusammenführen |
| Analyse – Zeitverlauf | Täglich + kumulativ | Monatlich + jährlich | 🔧 Beide Granularitäten zusammenführen |
| Analyse – Top-Artikel | Top 10 (Menge & Preis) | Top 30 Frequenz, Top 20 Ausgaben | 🔧 Erweitern (Lidl-Tabelle übernimmt REWE-Tiefe) |
| Analyse – Preisentwicklung | ❌ Keine | ✅ Monatlicher Linien-Chart, Volatilität | 🏗️ Für Lidl komplett neu |
| Analyse – Kategorien | ❌ Keine | ✅ Donut-Chart | 🏗️ Kategorisierung für Lidl zuerst nachholen |
| Analyse – Wochentag | ❌ Keine | ✅ Balken + Linie (Trips & Avg) | ✅ 1:1 übernehmen |
| Analyse – Inflations-Tracker | ❌ Keine | ✅ Erst/Letzt-Preis, % Änderung | ✅ 1:1 übernehmen |
| Analyse – Preis-Alarm | ❌ Keine | ✅ Letzte Zahlung > 10 % über Ø | ✅ 1:1 übernehmen |
| Analyse – Saisonale Muster | ❌ Keine | ✅ Jahreszeiten × Kategorien | ✅ 1:1 übernehmen |
| Analyse – Warenkorbpaare | ❌ Keine | ✅ Kombinations-Frequenzen (Top 50) | ✅ 1:1 übernehmen |
| Analyse – Verbrauch / Wiederbestellung | ❌ Keine | ✅ kg/Jahr, Stk/Jahr, Hält-Ø-Tage, Prognose | ✅ 1:1 übernehmen |
| Analyse – Ausgaben-Forecast | ❌ Keine | ✅ Hochrechnung aktueller Monat | ✅ 1:1 übernehmen |
| Analyse – Bonus/Loyalität | Lidl Plus Sparquote (3 Arten) | REWE Bonus (gesammelt, Guthaben, Ø-Rate) | 🔧 Superstore-spezifisch kapseln |
| Suche / Filter | Datumsfilter (Sidebar) | Textsuche Artikel + Kategorie-Dropdown | 🔧 Beides kombinieren |
| Belegansicht | ❌ Keine | ✅ Aufklappbare Zeilen mit Artikel-Details | ✅ 1:1 übernehmen |
| PDF/Original-Belegzugriff | ❌ Keine | ✅ PDF-Link pro Beleg | ⚠️ REWE: PDFs vorhanden; Lidl: kein lokales PDF, evtl. API-Deep-Link |
| Mehrland-/Mehrwährung | ✅ `--country` Flag | ❌ Keine | 🔧 Country-Konfiguration übernehmen, für beide nutzbar |
| CLI / Startmenü | ✅ Interaktives Menü (initial/update/exit) | Doppelklick `.command`-Skript + `--serve` | 🔧 Einheitliches CLI mit Superstore-Auswahl |
| Apple Mail Export | ❌ Keine | ✅ `export_rewe_mail.sh` | ✅ 1:1 beibehalten, als optionales Hilfsskript |
| Fortschrittsanzeige | ✅ `progress_display.py` (Rich) | ❌ Keine | 🔧 Auch für REWE-Import einbauen |

---

## 3. Detailanalyse nach Bereich

### 3.1 Datenpipeline & Import

#### Lidl (API-basiert)

```
Browser-Session
  └─ CookieExtractor (Firefox/Chrome/Datei)
       └─ LidlClient.get_tickets()          → Liste von Receipt-IDs
            └─ LidlClient.get_ticket_detail() → HTML-Boninhalt
                 └─ ReceiptParser / ItemsExtractor
                      └─ FileManager (lidl_receipts.json)
```

#### REWE (Datei-basiert)

```
EML / PDF-Dateien im import/-Ordner
  └─ process_eml() / process_pdf_direct()
       └─ pdfplumber → Rohtext
            └─ parse_receipt() (Regex)
                 └─ insert_receipt() / insert_items() (SQLite)
```

#### Gap & Handlungsbedarf

| # | Issue | Aufwand | Empfehlung |
|---|-------|---------|------------|
| G-1 | Keine gemeinsame Abstraktion | 🔧 mittel | Interface `ReceiptSource` mit Methoden `fetch_new()` → `List[NormalizedReceipt]` |
| G-2 | Verschiedene Ausgabeformate (JSON vs. SQLite) | ⚠️ hoch | Auf SQLite migrieren; JSON nur als Export |
| G-3 | Lidl: kein Kategorie-Feld in Items | 🔧 mittel | `categorize(name)` aus REWE nach Import anwenden |
| G-4 | REWE: keine Duplikat-ID wie Lidl | ✅ gelöst | UNIQUE(date, bon_nr, total) in DB ausreichend |
| G-5 | Lidl: `unit_price` und `quantity` vorhanden, aber nicht genutzt | ✅ einfach | Direkt für Verbrauchs-Analyse verwenden |

---

### 3.2 Datenmodell – Normalisiertes Zwischenformat

Beide Projekte liefern Kassenbons mit ähnlicher Struktur, aber unterschiedlichen Feldnamen.

#### Aktuell Lidl (JSON):
```json
{
  "purchase_date": "2024.12.01",
  "total_price": "15,49",
  "amount_saved": "1,20",
  "lidlplus_amount_saved": "0,50",
  "sticker_discount_amount": "0,30",
  "items": [
    { "name": "Banane", "price": "0,49", "quantity": "1", "unit": "stk" }
  ]
}
```

#### Aktuell REWE (SQLite):
```sql
receipts: date, time, market_id, bon_nr, total, source, bonus_earned, bonus_balance
items:     receipt_id, name, price, unit_price, quantity, tax, category
```

#### Vorschlag: Einheitliches Zielmodell (SQLite)

```sql
-- Kassen-/Superstore-Tabelle
stores (id, name, country, chain)  -- z.B. "Lidl DE", "REWE DE"

-- Belege
receipts (
  id            INTEGER PK,
  store_id      INTEGER REFERENCES stores(id),
  date          TEXT NOT NULL,       -- YYYY-MM-DD
  time          TEXT,                -- HH:MM
  market_id     TEXT,               -- Markt-Nummer (REWE) oder NULL (Lidl)
  external_id   TEXT,               -- Lidl Ticket-ID oder REWE Bon-Nr.
  total         REAL NOT NULL,
  source        TEXT,               -- Dateiname (REWE) oder "api" (Lidl)
  -- Loyalitäts-/Bonus-Felder
  bonus_earned  REAL,               -- REWE Bonus gesammelt
  bonus_balance REAL,               -- REWE Bonus Guthaben
  saved_plus    REAL,               -- Lidl Plus gespart
  saved_regular REAL,               -- Reguläre Rabatte gespart
  saved_sticker REAL,               -- Lidl Sticker-Rabatte
  UNIQUE(store_id, date, external_id, total)
)

-- Artikel
items (
  id          INTEGER PK,
  receipt_id  INTEGER REFERENCES receipts(id),
  name        TEXT NOT NULL,
  price       REAL NOT NULL,
  unit_price  REAL,                 -- EUR/kg oder EUR/Stk
  quantity    REAL DEFAULT 1,       -- Stück oder kg
  unit        TEXT DEFAULT 'stk',   -- 'stk' | 'kg'
  tax         TEXT,                 -- Steuerkennzeichen (REWE: A/B)
  category    TEXT                  -- aus CATEGORIES-Mapping
)

-- Verarbeitete Quelldateien (für REWE EML/PDF)
processed_files (filename TEXT PK, processed_at TEXT)
```

**Bewertung:** 🔧 mittlerer Aufwand – Lidl-JSON-Importer muss auf neues SQLite-Schema schreiben; REWE-Importer braucht `store_id`-Pflichtfeld.

---

### 3.3 Kategorisierung

| Aspekt | Lidl | REWE | Handlungsbedarf |
|--------|------|------|-----------------|
| Keyword-Mapping vorhanden | ❌ | ✅ 15 Kategorien, ~300 Keywords | 🔧 |
| Artikelnamen | Deutsch, gemischte Groß-/Kleinschreibung | Deutsch, GROSSBUCHSTABEN | 🔧 |
| Sonderzeichen | ✅ Umlaute | ✅ Umlaute (teilw. kodiert) | ✅ |

**Empfehlung:** REWE-`CATEGORIES`-Dict 1:1 übernehmen + Erweiterung um Lidl-spezifische Artikelbezeichnungen (z.B. "Lidl Backmischung", typische Eigenmarken). Da Lidl mixed-case-Artikelnamen hat und das Matching gegen `name.upper()` erfolgt, funktioniert der REWE-Code direkt – nach einem Test.

---

### 3.4 Dashboard / Frontend

Dies ist die wichtigste Architekturentscheidung:

| Kriterium | Streamlit (Lidl) | Selbst-gebautes HTML (REWE) |
|-----------|------------------|-----------------------------|
| Feature-Tiefe | Wenige Charts | Sehr reich (8 Tabs, 15+ Analysen) |
| Technologie-Aufwand | Python-Komfort | Chart.js-Wissen nötig |
| Live-Updates | ✅ Einfach via `st.rerun` | Neustart-Workflow nötig |
| Offline-fähig | ❌ Server nötig | ✅ Statische HTML-Datei |
| Styling | Streamlit-Default | Vollständig anpassbar (REWE-Rot) |
| Tab-Navigation | ❌ Sidebar | ✅ Sticky Nav mit 8 Tabs |
| Gruppen-Editor | ❌ | ✅ inkl. lokalem HTTP-Save-Server |
| Superstore-Switch | Muss gebaut werden | Muss gebaut werden |

**Empfehlung:** REWE-HTML-Ansatz als Basis nehmen (mehr Features, offline), **oder** vollständig zu Streamlit wechseln und alle REWE-Analysen portieren. Entscheidung vor Umsetzung treffen.

**Option A – HTML-Ansatz erweitern** (REWE als Basis):
- Header/Navigation: Superstore-Switcher (Lidl / REWE / Beide) hinzufügen
- Farbschema: Lidl = Gelb/Blau, REWE = Rot → dynamisch per CSS-Variable
- Bonus-Sektion: Shopspezifisch umschalten (Lidl Plus vs. REWE Bonus)
- Datenquelle: aus SQLite statt zwei getrennten Stores lesen

**Option B – Streamlit als Basis** (Lidl als Basis):
- Alle REWE-Tabs portieren (Preisentwicklung, Verbrauch, Extras, Gruppen usw.)
- Aufwand: ~5–8 Tage für Feature-Parität

---

### 3.5 Features: 1:1 übertragbar (✅)

Folgende REWE-Features können komplett ohne strukturelle Änderungen übernommen werden, sobald das Datenmodell harmonisiert ist:

| Feature | REWE-Code-Stelle | Übertragbarkeit |
|---------|-----------------|-----------------|
| Wochentag-Analyse | `weekday_raw`-Query + `weekdayChart` | ✅ reine SQL/JS-Logik |
| Inflations-Tracker | `inf_raw`-Query + `renderInflation()` | ✅ |
| Preis-Alarm (>10% über Ø) | `price_alarm`-Berechnung | ✅ |
| Saisonale Muster | `seasonal_raw`-Query + `seasonChart` | ✅ (braucht Kategorie-Feld) |
| Warenkorbpaare | `_pair_counts` via `itertools.combinations` | ✅ |
| Verbrauch kg/Jahr + Stk/Jahr | `_cons`-Berechnung | ✅ (braucht `unit_price` ≠ `price` für kg-Erkennung) |
| Wiederbestellungs-Prognose | `reorder`-Berechnung | ✅ |
| Ausgaben-Forecast | `_forecast`-Berechnung | ✅ |
| Preisschwankung (Volatilität) | `_price_vol`-Berechnung | ✅ |
| Preisentwicklungs-Chart | `price_by_item`-Query + `trendChart` | ✅ |
| Artikel-Gruppen-Editor | `groups.json` + HTTP-Save-Server | ✅ |
| Kategorien-Donut | `cat_stats`-Query + `catChart` | ✅ (braucht Kategorie-Feld) |
| Aufklappbare Belegzeilen | `toggleReceipt()` | ✅ |
| Apple Mail Export-Script | `export_rewe_mail.sh` | ✅ |
| Sortierbare Tabellen | `sortPositions()`, `sortReceipts()` usw. | ✅ |

---

### 3.6 Features: Anpassung nötig (🔧)

| Feature | Problem | Lösung |
|---------|---------|--------|
| Bonus-/Loyalitäts-Auswertung | Lidl: 3 Savings-Felder; REWE: 2 Bonus-Felder | Shopspezifische Sub-Komponente; im Dashboard via `store_id` oder Store-Filter steuern |
| Kategorisierung für Lidl | Keywords auf REWE-Artikelnamen optimiert | Keyword-Liste durch Lidl-Testdaten ergänzen; evtl. fuzzy-Match für Lidl-Eigenmarken |
| Inkrementeller Update-Workflow | Lidl: API-basiert mit Session; REWE: Datei-Hash | Gemeinsame `ImportState`-Klasse; Lidl-Pfad bleibt API, REWE-Pfad bleibt Datei |
| CLI | Getrennte Skripte | Einheitliches `main.py` mit `--store lidl|rewe|all` und weiterhin interaktivem Menü |
| Persistenz (JSON → SQLite für Lidl) | Lidl schreibt JSON, Dashboard liest JSON | Migrations-Skript + neuer SQLite-Writer in `FileManager` |
| PDF-Belegzugriff Lidl | Lidl hat keine lokalen PDFs | Option A: Deep-Link zur Lidl-Website für Beleg; Option B: API-Receipt-HTML als "Vorschau" im Dashboard speichern |
| Mehrland-Konfiguration | Nur Lidl hat `--country` | `StoreConfig` verallgemeinern: `{chain, country, currency, date_format}` |
| Fortschrittsanzeige für REWE | Kein Progress-Feedback bei großem Import | `progress_display.py` (Rich) aus Lidl in den REWE-Import-Workflow einbauen |

---

### 3.7 Features: Neu bauen (🏗️)

| Feature | Beschreibung | Aufwand |
|---------|-------------|---------|
| Superstore-Switcher im Dashboard | Filter/View für "Lidl", "REWE" oder "Alle zusammen" | mittel |
| Superstore-Vergleichs-Chart | Ausgaben Lidl vs. REWE über Zeit in einem Chart | mittel |
| Gemeinsamer Kategorie-Vergleich (Superstore) | Welcher Anteil meiner Obst-Käufe kommt von Lidl vs. REWE? | mittel |
| Datenmodell-Migration (Lidl JSON → SQLite) | Einmalig-Migrationsskript + dauerhafter SQLite-Writer | mittel |
| Store-Adapter-Interface | Abstrakter Basisklasse für Lidl + REWE (+ künftige Superstores) | gering |
| Keyword-Erweiterung Kategorien | Lidl-spezifische Artikel-Keywords hinzufügen | gering |
| Einheitliches Installationsskript / `requirements.txt` | Beide Projekte haben getrennte Dependencies | gering |

---

## 4. Dependencies – Vergleich & Gegenüberstellung

| Paket | Lidl | REWE | Kommentar |
|-------|------|------|-----------|
| `streamlit` | ✅ | ❌ | Nur wenn Option B (Streamlit-Dashboard) |
| `pandas` | ✅ | ❌ | Für Datenverarbeitung im Lidl-Dashboard |
| `requests` | ✅ | ❌ | Lidl-API-Client |
| `browser-cookie3` | ✅ | ❌ | Cookie-Extraktion |
| `rich` | ✅ | ❌ | Progress-Display |
| `pdfplumber` | ❌ | ✅ | REWE-PDF-Parser |
| `sqlite3` | stdlib | stdlib | Beide können nutzen |
| `chart.js` (CDN) | ❌ | ✅ | REWE-HTML-Dashboard |
| `email` (stdlib) | ❌ | ✅ | EML-Parsing |

**Minimalziel `requirements.txt` (kombiniert):**
```
requests
browser-cookie3
rich
pdfplumber
pandas          # optional, nur für Streamlit-Variante
streamlit       # optional, nur für Streamlit-Variante
```

---

## 5. Risiken & offene Entscheidungen

| ID | Risiko / Entscheidung | Priorität | Empfehlung |
|----|-----------------------|-----------|------------|
| R-1 | **Dashboard-Technologie** (Streamlit vs. HTML): betrifft den gesamten Umsetzungsaufwand | 🔴 kritisch | Entscheidung vor Start der Umsetzung |
| R-2 | **Persistenz**: JSON hat keine Schemavalidierung; SQLite ist Voraussetzung für SQL-basierte Analysen | 🔴 kritisch | SQLite einmalig migrieren |
| R-3 | Lidl-Artikelnamen passen nicht zu REWE-Keyword-Listen | 🟡 mittel | Testlauf mit echten Lidl-Daten; manuelle Ergänzung |
| R-4 | REWE-Gruppen-Editor benötigt localhost-Server (Port 7331) | 🟡 mittel | Nur in Streamlit-Option relevant (dort nativ lösbar) |
| R-5 | Lidl-API-Auth funktioniert nicht dauerhaft ohne Browser-Session | 🟢 bekannt | Kein neues Problem; bestehende Lösung beibehalten |
| R-6 | Monatliche Ausgaben-Granularität: Lidl-Dashboard zeigt täglich, REWE monatlich | 🟢 gering | Beide Ansichten anbieten (Radio-Button, existiert bereits in Lidl) |

---

## 6. Empfohlene Umsetzungsreihenfolge

```
Phase 1 – Fundament (Datenmodell)
  ├─ [ ] Gemeinsames SQLite-Schema definieren (stores, receipts, items)
  ├─ [ ] REWE-Importer: store_id-Feld hinzufügen
  ├─ [ ] Lidl-Importer: auf SQLite-Writer umstellen
  └─ [ ] Migration: vorhandene lidl_receipts.json → SQLite

Phase 2 – Kategorisierung für Lidl
  ├─ [ ] categorize()-Funktion aus REWE übernehmen
  ├─ [ ] Testlauf mit echten Lidl-Daten; fehlende Keywords ergänzen
  └─ [ ] Kategorie beim Lidl-Import automatisch setzen

Phase 3 – Gemeinsames CLI
  ├─ [ ] Einheitliches main.py mit --store lidl|rewe
  └─ [ ] Gemeinsames requirements.txt

Phase 4 – Dashboard-Zusammenführung (nach Architekturentscheidung R-1)
  ├─ [ ] Superstore-Filter / -Switcher
  ├─ [ ] Alle REWE-Analysen als Tabs verfügbar machen (für Lidl-Daten)
  └─ [ ] Superstore-Vergleichs-Charts

Phase 5 – Nice-to-have
  ├─ [ ] Keyword-Erweiterung via UI (statt groups.json)
  ├─ [ ] Lidl-PDF/Bon-Vorschau im Dashboard
  └─ [ ] --country-Flag auch für REWE (z.B. Österreich)
```

---

## 7. Zusammenfassung

**Sofort 1:1 übernehmbar (0 Architekturaufwand):**
Alle 15 REWE-Analysen (Tabellen + Charts) sind reine SQL-Abfragen + JS/HTML und funktionieren auf dem vereinheitlichten Datenmodell direkt – sobald die Tabellen `receipts` und `items` mit `store_id` und `category` befüllt sind.

**Hauptarbeiten vor dem Zusammenführen:**
1. Datenbankentscheidung (SQLite) treffen → ~1 Tag
2. Dashboard-Entscheidung (HTML vs. Streamlit) treffen → ~0.5 Tag
3. Lidl-Importer auf SQLite umschreiben → ~1–2 Tage
4. Kategorisierung für Lidl-Artikel testen/ergänzen → ~0.5 Tag

**Realistischer Gesamtaufwand bis Feature-Parität:**  
~1–2 Wochen (mit klaren Entscheidungen bei R-1 und R-2).

