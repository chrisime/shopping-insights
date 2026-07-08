# Gap-Analyse: `shopping-insights` vs. `rewe-ebon-analyse`

> Erstellt: Juli 2026
> Basis: [`nochsoeiner/rewe-ebon-analyse`](https://github.com/nochsoeiner/rewe-ebon-analyse) v1.0

---

## 1. Legende

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Vorhanden und funktional |
| 🔧 | Teilweise vorhanden / reduziert |
| ❌ | Fehlt vollständig |

---

## 2. Überblick – Dashboard / Analyse-Tabs

| Feature | `rewe-ebon-analyse` | `shopping-insights` | Handlungsbedarf |
|---------|---------------------|-------------------|-----------------|
| Dashboard (Monatsausgaben, Jahresübersicht) | ✅ tab | ✅ | — |
| Top-Artikel (Häufigkeit & Ausgaben) | ✅ Top 30 + Top 20 | ✅ Top 5–50, sortierbar | 🔧 Referenz zeigt gruppierte Ansicht (canonical names via `groups.json`) |
| Kategorien (Donut-Chart) | ✅ | ❌ | 🏗️ Neu |
| Wochentag-Analyse | ✅ | ✅ | — |
| Bonus-Guthaben & Bonus-Rate | ✅ | ✅ | 🔧 referenz zeigt Bonus-Verlauf monatlich |
| Saisonale Muster (normalisiert) | ✅ | ❌ | 🏗️ Neu |
| Monatsforecast | ✅ | ❌ | 🏗️ Neu |
| Preis-Alarm (>10% über Ø) | ✅ | ❌ | 🏗️ Neu |
| Inflations-Tracker (Erst-/Letztpreis) | ✅ | ❌ | 🏗️ Neu |
| Preisentwicklung (Einzelartikel-Chart) | ✅ | ❌ | 🏗️ Neu |
| Größte Preisschwankung / Stabilste Preise | ✅ | ❌ | 🏗️ Neu |
| Kürzlich gestiegen (90d vs. älter) | ✅ | ❌ | 🏗️ Neu |
| Warenkorbanalyse (Paar-Frequenzen) | ✅ Top 50 | ❌ | 🏗️ Neu |
| Einkaufszettel (Auto-Vorschläge) | ✅ | ❌ | 🏗️ Neu |
| Verbrauch (kg/Jahr, Stk/Jahr) | ✅ | ❌ | 🏗️ Neu |
| Haltbarkeit & Wochenverbrauch | ✅ | ❌ | 🏗️ Neu |
| Wiederbestellungs-Prognose | ✅ | ❌ | 🏗️ Neu |
| Alle Positionen (suchbar, sortierbar) | ✅ | 🔧 | 🔧 Nur API-Suche, keine Frontend-Tabelle |
| Kategorie pro Artikel klickbar ändern | ✅ | ❌ | 🏗️ Neu |
| €/kg für Gewichtsartikel | ✅ | ❌ | 🏗️ Neu |
| Alle Belege (aufklappbar + PDF-Link) | ✅ | 🔧 | 🔧 Receipt-Liste via API, aber keine expandierbare Detailansicht |
| Artikel-Gruppen (Browser-Editor) | ✅ | ❌ | 🏗️ Neu |
| Export JSON | ❌ | ✅ | Nur in shopping-insights |
| Lidl-Unterstützung | ❌ | ✅ | Nur in shopping-insights |
| Lidl Plus / Sticker / Discount-Tracking | ❌ | ✅ | Nur in shopping-insights |
| Dashboard-Import-UI (SSE) | ❌ | ✅ | Nur in shopping-insights |
| Multi-Retailer-Filter | ❌ | ✅ | Nur in shopping-insights |
| Automatischer Mail-Import (launchd) | ✅ | ❌ | 🏗️ Neu |

---

## 3. Detailanalyse

### 3.1 Preisentwicklung (komplett fehlend)

Das Referenzprojekt hat einen eigenen Tab mit 5 Untersektionen:

| Sub-Feature | Beschreibung | SQL/Logik |
|-------------|-------------|-----------|
| **Preishistorie** | Liniendiagramm pro Artikel mit Monats-Ø, Dropdown zur Artikelauswahl, Vorauswahl Top-10 | `GROUP BY name, substr(date,1,7)` |
| **Preisschwankung** | Tabelle: Artikel mit Min/Max/Ø/Letztpreis, Schwankung in %, Anzahl Käufe | `price_by_item`-Dict, Swing = (max-min)/avg |
| **Kürzlich gestiegen** | Vergleich Ø letzte 90 Tage vs. Ø 91–455 Tage davor, Schwellwert >10% | Zwei Zeitfenster per `date()` |
| **Preis-Alarm** | Letzter Preis >10% über historischem Ø | `_ph_map` pro Artikel |
| **Inflations-Tabelle** | Erster vs. letzter Preis pro Artikel (min. 3 Käufe), Änderung in % | Erste/letzte Zeile pro Artikel |

**Aufwand:** ~2–3 Tage (SQL-Queries + Vue-Chart-Komponenten + Filter)

---

### 3.2 Saisonale Muster (fehlt)

Referenz gruppiert Ausgaben nach Quartal (Frühling/Sommer/Herbst/Winter) × Kategorie, normalisiert über Anzahl der Vorkommen jeder Saison im Datensatz.

**Aufwand:** ~0.5 Tage (SQL + gestapeltes Balkendiagramm)

---

### 3.3 Monatsforecast (fehlt)

Hochrechnung des aktuellen Monats basierend auf Tagesrate × Monatstage, Vergleich mit Ø der letzten 6 Monate.

**Aufwand:** ~0.5 Tage

---

### 3.4 Verbrauch & Wiederbestellung (komplett fehlend)

| Sub-Feature | Beschreibung |
|-------------|-------------|
| **Jahresverbrauch kg** | Gewichtsartikel: kg/Jahr |
| **Jahresverbrauch Stk** | Stückartikel: Stk/Jahr |
| **Haltbarkeit** | Tage pro Einheit (Stück + kg vereint) |
| **Wochenverbrauch** | Was geht pro Woche durch |
| **Wiederbestellungs-Prognose** | Durchschnittliches Intervall, nächster Kauf, Konfidenz (CV), Saisonalitätserkennung |

**Aufwand:** ~2–3 Tage (Berechnungslogik + Vue-Komponenten)

---

### 3.5 Warenkorbanalyse (fehlt)

Häufigste Artikel-Paare in einem Beleg (Top 50, min. 3 gemeinsame Käufe), Gruppen-bewusst.

**Aufwand:** ~1 Tag (SQL + Heatmap/Bubble-Chart)

---

### 3.6 Einkaufszettel (fehlt)

Auto-Vorschläge basierend auf Wochenverbrauch und Kaufintervall, Karten-Layout mit Kategorie-Emoji, eigene Einträge, Kopieren/Drucken. Rein frontendseitig, keine Backend-Logik nötig.

**Aufwand:** ~1–2 Tage (Vue-Komponente, clientseitig)

---

### 3.7 Artikel-Gruppen (fehlt)

| Feature | Beschreibung |
|---------|-------------|
| **groups.json** | Mapping Gruppenname → Artikelnamen-Liste |
| **Browser-Editor** | Im Browser direkt editierbar via localStorage + HTTP-Save-Server (Port 7331) |
| **Gruppen-Wirkung** | Gruppierung wirkt auf Dashboard (Top-Artikel), Verbrauch und Warenkorbanalyse |
| **Auto-Vorschlag** | Cluster-Vorschlag basierend auf erstem signifikanten Wort |

**Aufwand:** ~1–2 Tage (JSON-Datei + Vue-Editor + Server-Endpoint)

---

### 3.8 Belege-Ansicht (unvollständig)

Referenz zeigt aufklappbare Zeilen mit Detailansicht inkl. PDF-Link. shopping-insights hat eine `GET /receipts` API aber keine Frontend-Komponente dafür.

**Aufwand:** ~1 Tag (Vue-Komponente + PDF-Link-Handling)

---

### 3.9 Kategorie-Override (fehlt)

Referenz speichert `categories_override.json` via Browser-Editor (Klick auf Badge in "Alle Positionen"), Override gilt für alle gleichlautenden Artikel.

**Aufwand:** ~1 Tag (JSON + Inline-Edit)

---

## 4. Was shopping-insights hat, das rewe-ebon-analyse nicht hat

| Feature | Nutzen |
|---------|--------|
| Lidl-Unterstützung | Beide Händler in einem Tool |
| Vue-Dashboard | Modernes, reaktives Frontend |
| Import-Job-System (SSE) | Live-Progress beim Import |
| Multi-Retailer-Filter | Lidl/REWE/Alle vergleichen |
| Lidl Plus / Sticker / Discount | 3 separate Rabatt-Typen |
| Pfand-Tracking | Pfand-Rücknahmen erfasst |
| Zahlungsarten | Mehrere Payment-Methoden |
| JSON-Export | Filter-Export als JSON-Download |
| Backend-API | Erweiterbar für Drittanbieter |

---

## 5. Empfohlene Reihenfolge

```
Phase 1 – Queries + Datenbasis
  ├─ Verbrauch (kg/Jahr, Stk/Jahr, Haltbarkeit, Wochenverbrauch)
  ├─ Wiederbestellungs-Prognose
  ├─ Warenkorbanalyse (Paar-Frequenzen)
  └─ Preisentwicklung (alle 5 Sub-Features)

Phase 2 – Frontend-Komponenten
  ├─ Artikel-Gruppen (groups.json + Editor)
  ├─ Kategorie-Override (categories_override.json)
  ├─ Belege-Ansicht (expandierbar + PDF-Link)
  ├─ Alle Positionen (Frontend-Tabelle)
  └─ Kategorie-Donut

Phase 3 – Fortgeschrittene Analysen
  ├─ Saisonale Muster
  ├─ Monatsforecast
  └─ Einkaufszettel

Phase 4 – Automatisierung
  └─ Automatischer Mail-Import (launchd + AppleScript)
```

---

## 6. Zusammenfassung

| Kategorie | ✅ | 🔧 | ❌ |
|-----------|----|-----|-----|
| Dashboard-Basics | 5 | 1 | 2 |
| Preisentwicklung | 0 | 0 | 5 |
| Verbrauch/Prognose | 0 | 0 | 4 |
| Artikel-Verwaltung | 0 | 2 | 3 |
| Gruppen/Kategorien | 0 | 0 | 3 |
| Sonstige Analysen | 0 | 0 | 3 |
| Automatisierung | 0 | 0 | 1 |

**Gesamt:** ~10–15 Tage Aufwand für Feature-Parität (ohne Automatisierung).
