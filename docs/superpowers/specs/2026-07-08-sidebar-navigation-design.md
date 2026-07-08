# Sidebar-Navigation und Filter-Aufteilung

> Erstellt: 2026-07-08

## Ziel

Das Dashboard von einer vertikalen Single-Page-Ansicht in ein Sidebar-Layout mit getrennten Bereichen umbauen. Die Filterung soll aufgeteilt werden: allgemeine Filter bleiben im Kopf, artikelspezifische Filter erscheinen nur im Artikel-Bereich.

## Layout

```
┌───────┬────────────────────────────────────────────┐
│  ☰    │  Shopping Analyzer           [JSON Export] │
│       │  ┌──────────────────────────────────────┐  │
│  Icon  │  │ Händler | Start | Ende | Granu | … │  │
│  +     │  └──────────────────────────────────────┘  │
│  Label │                                             │
│        │  ┌──────────────────────────────────────┐  │
│  📥    │  │                                      │  │
│  Im-   │  │   Active content per sidebar tab     │  │
│  port  │  │                                      │  │
│        │  └──────────────────────────────────────┘  │
│  💰    │                                             │
│  Aus-  │                                             │
│  geben │                                             │
│        │                                             │
│  📊    │                                             │
│  Ein-  │                                             │
│  kauf  │                                             │
│        │                                             │
│  🛒    │                                             │
│  Arti- │                                             │
│  kel   │                                             │
└───────┴────────────────────────────────────────────┘
```

- Sidebar links: vertikale Leiste, umschaltbar zwischen Expanded (Icon + Label) und Collapsed (nur Icon)
- Content-Bereich rechts: Header-Zeile (Titel + Export), globale Filter, dann der aktive Tab-Inhalt

## Sidebar-Verhalten

- Zustand `sidebarCollapsed` als `ref<boolean>` in `DashboardPage.vue`
- Umschalt-Button (☰) oben in der Sidebar
- Expanded: ~200px breit, collapsed: ~56px (nur Icons)
- Alle 4 Einträge zeigen ein Icon (Emoji oder SVG) als visuelle Kennung

## Tab-Struktur

```typescript
type SidebarTab = "import" | "ausgaben" | "einkauf" | "artikel";
```

- `activeTab` als `ref<SidebarTab>` mit Default `"ausgaben"`
- Jeder Tab zeigt eine andere Auswahl der `payload.sections`
- Die Daten werden weiterhin einmal geladen (gleicher `useDashboard()`-Call), nur die Anzeige wird pro Tab gefiltert

### Import (📥)
- `ImportJobControls` (wie aktuell)
- Keine Dashboard-Sections

### Ausgaben (💰)
- KPIs (DashboardKpiGrid) → `section.kind === "metrics"`
- Ausgaben über Zeit (TrendChartPanel) → `section.kind === "time_series"`
- Globale Filter sind im Kopf sichtbar

### Einkaufsverhalten (📊)
- Wochentag-Analyse (WeekdayPanel) → `section.kind === "weekday"`
- Globale Filter im Kopf

### Artikel (🛒)
- DashboardFilterBar (NUR mit Artikelsuche + Einträge pro Seite)
- TopItemsPanel (mit Pagination)
- Globale Filter im Kopf
- Die Felder Händler/Datum/Granularität/Ansicht/Sortierung sind im DashboardFilterBar ausgeblendet, nur search + topLimit bleiben sichtbar

## Filter-Aufteilung

### Im Seitenkopf (immer sichtbar)
- Händler (Select)
- Startdatum (Date)
- Enddatum (Date)
- Zeitgranularität (Select)
- Ansicht (Select)
- Sortieren nach (Select)

### Nur im Artikel-Tab
- Artikelsuche (Text)
- Einträge pro Seite (Select 10/20/50)

## Dateiänderungen

### Neu
- `web/src/components/DashboardSidebar.vue` — Sidebar-Komponente mit Collapse-Toggle

### Änderungen
- `web/src/components/DashboardPage.vue` — Layout von vertikal zu Sidebar+Content umbauen, Tab-Steuerung
- `web/src/components/DashboardFilterBar.vue` — Optionales Ausblenden der globalen Filter (prop `showGlobalFilters`)
- `web/src/components/TopItemsPanel.vue` — unverändert
- `web/src/components/DashboardFilterBar.vue` — optional: `global`-Prop steuert welche Felder gerendert werden

## Umsetzungsreihenfolge

1. `DashboardSidebar.vue` erstellen
2. `DashboardPage.vue` Layout umbauen (Sidebar + Content-Bereich)
3. `DashboardFilterBar.vue` um `global`-Prop erweitern
4. Tab-Logik implementieren (activeTab steuert sichtbare Sections)
5. Build + Tests validieren
