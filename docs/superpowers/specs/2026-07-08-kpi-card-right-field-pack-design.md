# KPI Card Right-Field Alignment Fix

## Problem
Rechte Label+Value-Paare in KPI-Cards schweben in der Mitte, weil `xl:grid-cols-4` die 2 Felder auf 4 Spalten verteilt. Die zweite Spalte endet bei 50% statt am rechten Card-Rand.

## Design
- `xl:grid-cols-4` entfernen, nur `sm:grid-cols-2` behalten
- Alle Multi-Feld-Cards haben exakt 2 Felder → passt

## Files
- `web/src/components/DashboardKpiGrid.vue` — eine CSS-Klasse ändern
