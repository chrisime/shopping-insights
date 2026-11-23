## Why

The Vue dashboard has grown through successive feature work, and its component boundaries should be reviewed as a whole rather than optimized one component at a time. A deliberate cleanup can make responsibilities, shared logic, and test seams easier to understand while avoiding both duplicated code and abstractions that obscure simple behavior.

## What Changes

- Review the dashboard components, composables, utilities, and related tests for responsibility boundaries, duplicated logic, unnecessary abstraction, testability, and maintenance cost.
- Treat `DashboardPage.vue`, `ImportJobControls.vue`, `ReceiptViewer.vue`, and `TrendBarChart.vue` as explicit review targets because of their size and breadth of responsibilities.
- Split retailer-specific KPI ownership currently concentrated in `DashboardKpiGrid.vue` (REWE, Lidl, and Rossmann) into retailer-focused components or modules when they have distinct structure or responsibility.
- Refactor the frontend where the review identifies a concrete improvement: keep components focused on presentation and coordination, put genuinely shared state or flows in composables, and keep reusable pure logic in utilities.
- Share KPI presentation only where the retailers genuinely have the same rendering responsibility; avoid a generic renderer or extra layers when they make the code harder to follow.
- Extract or consolidate components and logic only where the resulting boundary makes ownership and behavior clearer; do not introduce layers, generic frameworks, or indirection without a demonstrated need.
- Preserve existing user-visible behavior, API contracts, filter values, and dependencies.
- Add or adjust focused tests around extracted responsibilities and shared logic; retain the full frontend test, check, typecheck, and build gates.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `module-responsibilities`: Add explicit frontend component, composable, utility, and retailer-KPI responsibility expectations while preserving existing dashboard behavior and API contracts.

## Impact

- Affected areas: `web/src/components/DashboardPage.vue`, `ImportJobControls.vue`, `ReceiptViewer.vue`, `TrendBarChart.vue`, and `DashboardKpiGrid.vue`; related components, `web/src/composables/`, `web/src/utils/`, and corresponding frontend tests as justified by the review.
- No backend, API, dependency, or user-visible feature changes are intended.
- The existing `module-responsibilities` capability remains applicable as a general structural principle.
