## 1. Establish behavior and interfaces

- [x] 1.1 Run the focused existing tests for dashboard composition, import controls, receipt modals, KPI cards, and trend chart before refactoring.
- [x] 1.2 Record the props, emitted events, and API payloads that the reviewed components must preserve.

## 2. Give retailer KPI rules clear ownership

- [x] 2.1 Inventory retailer-specific KPI fields and visibility rules for Lidl, REWE, dm, and Rossmann across the dashboard payload and frontend types; confirm whether dm currently has dedicated KPI data before deciding its component/module boundary.
- [x] 2.2 Move current retailer-specific KPI definitions and visibility rules out of `DashboardKpiGrid.vue` into retailer-focused components or modules, keeping general spending KPIs separate.
- [x] 2.3 Keep shared KPI card rendering only where the retailers use the same presentation responsibility; add focused tests for retailer-specific output, missing fields, and Rossmann coupon visibility.

## 3. Refactor dashboard and import responsibilities

- [x] 3.1 Refactor `DashboardPage.vue` only where a cohesive page responsibility can be given a clear interface; add or update focused tests for page composition and interactions.
- [x] 3.2 Separate authentication/request-form responsibilities from progress/status presentation in `ImportJobControls.vue` only where the interface is narrow; test retailer defaults, authentication choices, and emitted `ImportStartRequest` payloads.

## 4. Refactor receipt and chart responsibilities

- [x] 4.1 Keep `ReceiptModal.vue` and `ReceiptListModal.vue` as focused data-source wrappers over `useReceiptBrowser`; extract a cohesive receipt-view responsibility from `ReceiptViewer.vue` only when it improves testability and ownership.
- [x] 4.2 Preserve the D3/SVG lifecycle in `TrendBarChart.vue`; extract only cohesive DOM-independent calculations or directly testable rendering helpers, with tests for tooltip, hover, period selection, and chart updates.

## 5. Verify the cleanup

- [x] 5.1 Run the full frontend test suite, `vp check`, typecheck, and build.
- [x] 5.2 Review the final diff to confirm no user-visible behavior, API contracts, retailer/filter values, or dependencies changed, and validate the OpenSpec change strictly.

## Contract inventory

- `ImportJobControls.vue`: preserve the `retailer`, `running`, `progress`, `message`, `error`, and `technicalError` inputs; `update:retailer` and `start-import` events; and the `ImportStartRequest` payload fields, including REWE `customer_id` and Rossmann credentials.
- `ReceiptViewer.vue`: preserve its `title`, `visible`, `loading`, `error`, `receipts`, `currentIndex`, and `highlightMatched` inputs, plus `close` and `update:currentIndex` events.
- Receipt wrappers: preserve `/receipts/by-item` parameters (`name`, optional `retailer`) and `/receipts/by-date` parameters (`start_date`, `end_date`, optional `retailer`) through the current API helpers.
- `TrendBarChart.vue`: preserve `items`, `granularity`, and `monthLabels` inputs and its `select-period` event; period selection continues to drive the date-range receipt flow.
- `DashboardKpiGrid.vue`: preserve its `MetricsRow` input and visible KPI values, groupings, and omission rules for incomplete or zero-value retailer data.
- `DashboardPage.vue`: preserve page-filter values, child component props/events, import/export behavior, and modal selection flow.
- KPI inventory finding: current retailer-specific dashboard KPI keys are for REWE, Lidl, and Rossmann; no dm-specific KPI fields are present in the dashboard builder or `DashboardKpiGrid.vue`. `dm_payback_points` is receipt-level data, not a dashboard KPI.

## Implementation findings

- `DashboardPage.vue` remains the page composition boundary: its state and event wiring are already explicit, and splitting sections into wrappers would add indirection rather than a distinct responsibility.
- `ImportJobControls.vue` now owns retailer/authentication inputs and request emission; `ImportJobProgress.vue` owns progress, status, and technical-error presentation.
- `ReceiptViewer.vue` remains a cohesive shared receipt experience, while `ReceiptModal.vue` and `ReceiptListModal.vue` remain data-source wrappers using `useReceiptBrowser`; no sub-view extraction was justified.
- `TrendBarChart.vue` retains D3/SVG lifecycle and DOM interactions; pure chart/period calculations were already isolated in `utils/chart.ts` and `utils/period.ts`, so no further helper extraction was warranted.
