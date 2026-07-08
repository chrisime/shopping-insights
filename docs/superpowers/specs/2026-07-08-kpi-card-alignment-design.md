# KPI Card Field Alignment

## Problem
Innerhalb jeder Kennzahlen-Card sollen primäre Metriken linksbündig und sekundäre Metriken rechtsbündig ausgerichtet sein. Beispiel: "Ausgaben gesamt" links, "Ausgaben ohne Rabatte" rechts.

## Scope
Nur `DashboardKpiGrid.vue`. Die anderen Panels (TopItemsPanel, WeekdayPanel, TrendChartPanel) sind bereits korrekt ausgerichtet.

## Design
- `rightAlignFields`-Set entfernen (keine wartungsintensive explizite Feldliste mehr)
- Im `v-for="(field, fi)"` die Position nutzen: `fi === 1` → `justify-items-end text-right`
- Cards mit nur einem Feld (Pfandrückgabe) bleiben linksbündig

## Implementation
1. `DashboardKpiGrid.vue`: Template-Änderung — Alignment per Index statt per Set
2. `rightAlignFields`-Set löschen (unused)
3. Tests: prüfen ob 38 Frontend-Tests + Build noch grün sind

## Files
- `web/src/components/DashboardKpiGrid.vue`
