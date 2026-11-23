## Context

The Vue dashboard already separates shared state and API work into composables and API modules, and reusable formatting and chart calculations into utilities. Several components nevertheless coordinate multiple concerns:

- `DashboardPage.vue` owns dashboard state wiring, import state wiring, export handling, tab/selection state, and composition of the dashboard views.
- `ImportJobControls.vue` combines retailer/authentication choices, credentials and request construction, and progress/status presentation.
- `ReceiptViewer.vue` combines modal framing, paging controls, receipt metadata, item rows, and totals. `ReceiptModal.vue` and `ReceiptListModal.vue` already reuse it and `useReceiptBrowser`.
- `TrendBarChart.vue` combines SVG/D3 drawing, axes, month markers, bar labels, tooltip content/visibility, and click/hover behavior.
- `DashboardKpiGrid.vue` owns common card rendering and field formatting alongside retailer-specific card definitions and visibility rules for REWE, Lidl, and Rossmann.

The accepted proposal identifies these as review targets, not as an instruction to split every large file. The refactor must make ownership easier to follow without changing dashboard behavior or introducing abstractions that cost more than they clarify.

The current component flow is:

```text
DashboardPage.vue
  ├── useDashboard ──> Dashboard API
  ├── useImportJob ──> Import API
  ├── Dashboard Panels
  │     └── TrendChartPanel ──> TrendBarChart
  ├── ImportJobControls
  ├── ReceiptModal / ReceiptListModal
  │     └── useReceiptBrowser ──> Dashboard API
  │           └── ReceiptViewer ──> ReceiptCouponSavings
  └── DashboardKpiGrid
        └── retailer-specific KPI definitions
```

The current ADR set was reviewed. ADR-0006 is superseded by ADR-0007; no in-force ADR prescribes Vue component structure. ADR-0003's preference for a thin shared path over unnecessary abstraction is consistent with this cleanup but applies to backend workflows.

## Goals / Non-Goals

**Goals:**

- Give each resulting component, composable, and utility a cohesive, easy-to-name responsibility.
- Make retailer-specific KPI definitions and rules owned by retailer-focused modules or components where their structure or behavior differs.
- Keep genuinely shared KPI presentation in a small shared view only when it reduces duplication without hiding retailer-specific behavior.
- Make extracted logic independently testable where it is pure or has a stable, narrow interface; preserve focused component tests for rendering and interaction.
- Keep the implementation reviewable through incremental, responsibility-based changes.

**Non-Goals:**

- Change user-visible dashboard behavior, API requests/contracts, retailer codes, or filter values.
- Split components solely to reduce line count or meet a size target.
- Introduce a generic component framework, state-management library, dependency-injection layer, or new dependency.
- Move D3 DOM manipulation into abstractions that are harder to understand or test than the current component.

## Decisions

### Keep `DashboardPage.vue` as the page-level composition boundary

`DashboardPage.vue` remains responsible for connecting page state to view components and selecting the active dashboard view. During implementation, move a coherent secondary responsibility out only when doing so gives it an independent interface and test seam. Candidate areas include export state/action and modal/section coordination, but the final split must follow the actual coupling rather than line count.

**Alternative considered:** Turn each tab or every section into another wrapper component. Rejected as a default because wrapper-only components would add navigation and indirection without necessarily creating ownership boundaries.

### Separate import form concerns from progress display only where their interfaces are stable

Treat authentication selection, retailer-specific credential inputs, import request construction, and job progress/status as distinct responsibilities for review. Preserve the current typed `ImportStartRequest` event boundary. Extract form sections or progress presentation only when their inputs/outputs remain narrow and tests can exercise them without mounting unrelated dashboard behavior.

**Alternative considered:** Replace the form with a configuration-driven renderer for every retailer and authentication mode. Rejected unless implementation demonstrates substantial repeated structure; configuration must not conceal meaningful retailer differences.

### Preserve a shared receipt viewer and keep the two modal wrappers focused

Keep the existing division in which `ReceiptModal.vue` and `ReceiptListModal.vue` choose their data loaders and titles, `useReceiptBrowser` handles loading/navigation state, and `ReceiptViewer.vue` renders the shared receipt experience. Within the viewer, consider extracting receipt metadata or item-list presentation only if that unit is cohesive and has a useful test boundary. Keep Rossmann coupon details retailer-specific.

**Alternative considered:** Duplicate separate receipt dialogs for item search and date selection. Rejected because both flows already share presentation and navigation.

### Keep chart rendering understandable and keep pure logic outside the DOM layer

Keep D3/SVG lifecycle and DOM operations close to the chart component. Reuse existing pure functions in `web/src/utils/chart.ts` and `web/src/utils/period.ts`; move additional calculations there only when they are DOM-independent. Split rendering helpers into another module only if the functions form a cohesive, small interface that is clearer and directly testable; do not create a chart-rendering framework.

**Alternative considered:** Move all D3 drawing into a large generic chart utility or composable. Rejected because the rendering lifecycle, event handlers, and SVG structure would become less visible and harder to test together.

### Give retailer-specific KPI rules clear ownership

Move REWE, Lidl, and Rossmann card definitions and retailer-specific visibility rules out of `DashboardKpiGrid.vue` into retailer-focused modules or section components. Retain shared formatting and card markup only for the common shape actually shared by these retailers. Keep general spending KPIs separate from retailer-specific KPI ownership. Test retailer visibility and output at the narrowest useful component/module boundary.

**Alternative considered:** Keep one large `DashboardKpiGrid.vue` with configuration arrays for every retailer. Rejected because it centralizes retailer knowledge and makes changes for one shop require editing a multi-retailer component.

**Alternative considered:** Create an independent full card renderer for every retailer. Rejected where it would duplicate identical markup; only retailer-specific behavior should be split.

### Use behavior-preserving, test-led slices

For each extraction, first preserve or add a focused test that captures the current behavior, then move one responsibility and run the narrow test. Finish with the full frontend test suite, `vp check`, typecheck, and build. Keep public component props/events and API payloads unchanged unless a necessary internal interface can change without affecting those contracts.

**Alternative considered:** Perform a broad all-at-once component rewrite. Rejected because it creates a large review surface and makes regressions harder to localize.

## Risks / Trade-offs

- [Risk] Splitting components can increase file count and navigation cost. -> [Mitigation] Require each new unit to own a cohesive responsibility and have a clear interface; do not extract solely for line count.
- [Risk] Moving retailer rules or chart event handling can subtly change visibility, formatting, accessibility, or click/hover behavior. -> [Mitigation] Add focused tests before moving the logic and preserve existing props, events, and API values.
- [Risk] A shared KPI renderer may either duplicate presentation or over-generalize retailer differences. -> [Mitigation] Extract only the common presentation that is evident after separating retailer ownership; keep retailer-specific decisions local.
- [Risk] The broad cleanup could produce an overly large review diff. -> [Mitigation] Organize implementation and commits in small responsibility-based slices and defer unrelated cleanup.

## Migration Plan

This is an internal frontend refactor with no data migration or deployment sequencing requirement. Work in small slices: capture current behavior in focused tests, extract or reorganize one responsibility, verify the affected tests, then proceed to the next target. After all slices, run the complete frontend test suite, `vp check`, typecheck, and build. Rollback consists of reverting the isolated refactor slice; no API or persisted-data compatibility changes are expected.

## Open Questions

- The exact child-component boundaries for `DashboardPage.vue`, `ImportJobControls.vue`, `ReceiptViewer.vue`, and `TrendBarChart.vue` remain implementation findings. Do not force a split where inspection shows a coherent component with an already clear interface.
- For retailer KPIs, the agreed direction is retailer-focused ownership; implementation should decide per shop whether a small component or a retailer-specific data module makes that ownership clearer, while sharing only genuinely common card rendering.
- No in-force ADR currently requires supersession for this frontend-only structural refactor.
