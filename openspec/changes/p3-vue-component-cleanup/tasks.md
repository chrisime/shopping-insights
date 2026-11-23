## 1. Establish behavior and interfaces

- [ ] 1.1 Run the focused existing tests for dashboard composition, import controls, receipt modals, KPI cards, and trend chart before refactoring.
- [ ] 1.2 Record the props, emitted events, and API payloads that the reviewed components must preserve.

## 2. Give retailer KPI rules clear ownership

- [ ] 2.1 Inventory retailer-specific KPI fields and visibility rules for Lidl, REWE, dm, and Rossmann across the dashboard payload and frontend types; confirm whether dm currently has dedicated KPI data before deciding its component/module boundary.
- [ ] 2.2 Move current retailer-specific KPI definitions and visibility rules out of `DashboardKpiGrid.vue` into retailer-focused components or modules, keeping general spending KPIs separate.
- [ ] 2.3 Keep shared KPI card rendering only where the retailers use the same presentation responsibility; add focused tests for retailer-specific output, missing fields, and Rossmann coupon visibility.

## 3. Refactor dashboard and import responsibilities

- [ ] 3.1 Refactor `DashboardPage.vue` only where a cohesive page responsibility can be given a clear interface; add or update focused tests for page composition and interactions.
- [ ] 3.2 Separate authentication/request-form responsibilities from progress/status presentation in `ImportJobControls.vue` only where the interface is narrow; test retailer defaults, authentication choices, and emitted `ImportStartRequest` payloads.

## 4. Refactor receipt and chart responsibilities

- [ ] 4.1 Keep `ReceiptModal.vue` and `ReceiptListModal.vue` as focused data-source wrappers over `useReceiptBrowser`; extract a cohesive receipt-view responsibility from `ReceiptViewer.vue` only when it improves testability and ownership.
- [ ] 4.2 Preserve the D3/SVG lifecycle in `TrendBarChart.vue`; extract only cohesive DOM-independent calculations or directly testable rendering helpers, with tests for tooltip, hover, period selection, and chart updates.

## 5. Verify the cleanup

- [ ] 5.1 Run the full frontend test suite, `vp check`, typecheck, and build.
- [ ] 5.2 Review the final diff to confirm no user-visible behavior, API contracts, retailer/filter values, or dependencies changed, and validate the OpenSpec change strictly.
