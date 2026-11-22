## Why

The dashboard's single "Kennzahlen" card mixes two different concerns: general
spending facts (total spend, receipt count, deposit, overall savings) and
retailer-specific discounts. Users cannot quickly separate "what did I spend"
from "how much did I save through discounts", especially when several retailers
contribute discounts. Splitting the card improves scanability and lets Rossmann
show the same "Preisvorteil" summary that Lidl already has.

## What Changes

- Split the single `metrics` dashboard section titled "Kennzahlen" into two
  sections:
  - **Allgemeine Informationen** — always present; contains Ausgaben,
    Kassenbons, Pfandrückgabe, and Gesamter Preisvorteil.
  - **Rabatte** — contains the existing Rewe, Lidl, and Rossmann discount card
    groups.
- Omit the "Rabatte" section entirely when no discount metrics exist (for
  example, dm-only data). When a discount-capable retailer is selected, keep the
  section visible even when all discount values are `0` (shows `0 €` / `0,0 %`).
- Add a Rossmann **Preisvorteil** card (total Rossmann discount amount and
  percentage) as the last card of the Rossmann group, mirroring Lidl's
  "Preisvorteil".
- The backend emits two `metrics` sections instead of one; the frontend renders
  each metrics section with only the cards whose backing fields are present.

## Capabilities

### New Capabilities

- `dashboard-kpi-cards`: Composition, grouping, and visibility rules for the
  dashboard KPI sections and their cards, covering general spending metrics and
  retailer discount metrics.

### Modified Capabilities

- None. No existing spec-level behaviour changes.

## Impact

- `api/services/dashboard_builders.py` — partition KPI metrics into two
  `DashboardSection(kind="metrics")` entries and conditionally omit "Rabatte".
- `web/src/components/DashboardKpiGrid.vue` — render card groups based on field
  presence; add the Rossmann "Preisvorteil" card.
- Backend tests: `tests/test_api_imports.py`, `tests/test_api_ui_dashboard.py`,
  `tests/test_dashboard_ui_model.py`, `tests/test_frontend_schema.py`.
- Frontend tests: `web/src/components/__tests__/DashboardKpiGrid.spec.ts`,
  `DashboardPage.spec.ts`, `DashboardPageExport.spec.ts`.
