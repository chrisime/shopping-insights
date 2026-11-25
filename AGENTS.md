# AGENTS.md

- For OpenSpec propose/apply/verify/archive workflows, use the local `openspec-git-discipline` skill to enforce proposal commits before apply and merge-before-archive discipline.

## Goal
- Python supermarket-ticket analyzer for Lidl and REWE.
- Downloads receipts, parses HTML/PDF data, normalizes it, stores it in SQLite, and serves KPI data to the Vue dashboard.

## Constraints & Preferences
- Vue is the only dashboard frontend.
- Use `pnpm` in `web/`.
- The frontend toolchain is Vite+ (`vp`): prefer `pnpm exec vp ...` or the pnpm scripts (`pnpm dev`, `pnpm test`, `pnpm build`).
- Always run the project-local `vp` from `web/node_modules/.bin`; a globally installed `vp` bundles its own Vitest and cannot resolve project-only deps such as `jsdom`.
- Use uv for backend commands.
- Lidl requests must retry with exponential backoff on 429/5xx.
- Shared auth-method resolution (`--browser` / `--cookies-file`) should stay common between Lidl and REWE.
- No third-party retry libraries; use plain `requests` + `time.sleep`.
- Address extraction should prefer positive validation and shared constants over blacklist heuristics.

## Current State
- Vue dashboard migration is on `main`.
- Streamlit entrypoint, renderer, and tests were removed.
- API routes exist for `ui`, `kpis`, `receipts`, `items`, `exports`, and `triggers`.
- The dashboard trend chart uses Apache ECharts with SVG rendering in `TrendCharts.vue`.
- Bar hover shows an ECharts tooltip with period, total, receipt count, average, and retailers.
- Bar click → ReceiptListModal via `GET /receipts/by-date` API.
- Monthly x-axis shows "Jan 2024" format.
- Time-series DTO includes `retailers` field (GROUP_CONCAT in SQL).
- Backend: 429 tests passing. Frontend: 110 tests (23 files) passing; `vp check`, `vp run typecheck`, and `vp build` succeed.
- Frontend toolchain migrated to Vite+ 1.7.0 (`vp`); lint/format run through Oxlint/Oxfmt, TS typecheck through tsrs, Vue SFCs through a `vue-tsc` task.

## Backend
- Start the API with `uv run --locked start-backend`.
- Use uv for Python commands, for example `uv run --locked python -m pytest -q`.
- The dashboard API lives at `api/main.py` and includes the `ui`, `kpis`, `receipts`, `items`, `exports`, and `triggers` routers.
- `GET /receipts/by-date` endpoint supports `start_date`, `end_date`, and optional `retailer` filter.
- Time-series KPIs in `storage/kpi_store.py` use `GROUP_CONCAT(DISTINCT s.retailer_code)` for retailer aggregation.
- `shared/kpi_dtos.py` defines `TimeSeriesRow` DTO with `retailers: list[str]`.
- Receipt fetching and parsing are driven by the workflow layer under `workflows/`.
- `workflows/local_import.py` provides the shared `import_local_sources()` import path (load → parse → validate → persist → skipped report) with an injectable `loader`; `workflows/import_workflow.py` holds the single thin `ImportWorkflow` base.
- `client/lidl_client.py` handles Lidl ticket page collection with retry/backoff.
- `workflows/lidl_workflow.py` uses `collect_lidl_receipt_ids()` and `get_lidl_ticket()`.
- `workflows/rewe_workflow.py` drives REWE initial/update imports.
- `fetch_tickets.py` is the main CLI entrypoint for imports, validation, and DB export.

## Ticket Fetching
- Interactive menu: `python fetch_tickets.py`
- LIDL initial import: `python fetch_tickets.py initial --retailer lidl --browser firefox`
- LIDL update from local JSONs: `python fetch_tickets.py update --retailer lidl`
- LIDL cookie validation: `python fetch_tickets.py check --retailer lidl --cookies-file lidl_cookies.json`
- LIDL export from SQLite: `python fetch_tickets.py export --retailer lidl --output-file lidl_receipts.json`
- REWE initial import: `python fetch_tickets.py initial --retailer rewe --cookies-file rewe_cookies.json`
- REWE update from local JSONs: `python fetch_tickets.py update --retailer rewe --output-dir tmp/rewe`
- REWE cookie validation: `python fetch_tickets.py check --retailer rewe --cookies-file rewe_cookies.json`
- REWE export from SQLite: `python fetch_tickets.py export --retailer rewe --output-file rewe_receipts.json`

## Recent Verification
- `uv run --locked python -m pytest -q` → 429 passed.
- `corepack pnpm exec vp test run` → 110 passed (23 files).
- `corepack pnpm exec vp check` → format, lint, and tsgo typecheck clean.
- `corepack pnpm exec vp run typecheck` → vue-tsc clean.
- `corepack pnpm exec vp build` → builds cleanly.
- `uv run --locked start-backend` then `curl http://localhost:8000/ui/dashboard` confirms API responds.

## Key Decisions
- Keep backend payloads section-based and reusable.
- Keep empty-database / no-receipts handling in the frontend payload layer.
- Use `shared.retailer_runtime.get_retailer_runtime()` for receipt JSON path resolution.
- Expose dashboard errors as structured payloads with `error_code` and `detail`.
- The ECharts range slider and wheel input control the visible trend periods.
- Tooltip hides with 200ms delay on mouseleave to prevent flicker.
- Use Vite+ as the single frontend toolchain (`vp dev/build/test/check`); keep `vite`/`vitest` catalog entries in `web/pnpm-workspace.yaml`.
- TypeScript stays on 6.0.x because `vue-tsc` 3.x requires the upstream `typescript/lib/tsc` entry, which TypeScript 7 (native) no longer exports; `vp check` uses tsrs independently.
- Frontend components stay presentational: pure logic lives in `web/src/utils/`, shared state in `web/src/composables/`, and API rows are typed in `web/src/types/dashboard.ts` (no `as any` casts in components).

## Relevant Files
- `api/main.py`
- `api/routes/`
- `api/services/` — split: `dashboard_models.py` (DTOs), `dashboard_builders.py` (pure builders), `dashboard_service.py` (thin service)
- `shared/kpi_dtos.py` — TimeSeriesRow with `retailers` field
- `storage/kpi_store.py` — GROUP_CONCAT in time-series SQL
- `client/lidl_client.py`
- `client/rewe_client.py`
- `client/dm_client.py` — dm purchase history / eBon / PDF client with 401 token refresh
- `config/dm_config.py` — dm endpoints, OAuth PKCE issuer/client, cookie + JSON file paths
- `auth/dm_auth.py` — OAuth 2.0 authorization-code + PKCE token mint (incl. login-form POST)
- `auth/dm_file_auth.py` — dm cookie-file loading + traffic-light diagnostics with live token check
- `auth/dm_browser_auth.py` — dm browser cookie extraction
- `parsing/dm_ebons_parser.py` — dm eBon JSON → shared receipt schema (pdfItems preferred, DAN merge)
- `parsing/dm_pdf_items_extractor.py` — item names/prices from dm eBon PDFs
- `parsing/dm_validator.py`
- `workflows/dm_workflow.py` — dm initial/update via shared `import_local_sources()`
- `cli/dm_menu.py` — interactive dm submenu
- `fetch_tickets.py`
- `workflows/` — de-abstraction: `local_import.py` (shared import path), `lidl_workflow.py`, `rewe_workflow.py`, `dm_workflow.py`, `import_workflow.py` (thin base); `import_pipeline.py` removed
- `auth/cookie_diagnostics.py` — split from `shared_file_auth.py` (session construction remains in `shared_file_auth.py`)
- `api/services/dashboard_errors.py`
- `api/services/dashboard_models.py` — dashboard DTOs
- `api/services/dashboard_builders.py` — pure dashboard builders
- `api/services/dashboard_service.py` — thin dashboard service
- `web/src/components/TrendCharts.vue` — trend chart with `useTrendECharts` and `useTimelineScroll`
- `web/src/components/TrendChartPanel.vue` — emits `select-period` for bar click
- `web/src/components/ReceiptViewer.vue` — shared receipt overlay/pager/detail
- `web/src/components/ReceiptModal.vue` / `ReceiptListModal.vue` — thin wrappers over `ReceiptViewer`
- `web/src/composables/useReceiptBrowser.ts` — receipt loading + navigation for both modals
- `web/src/components/DashboardPage.vue` — orchestrates modal + period state
- `web/src/api/http.ts` — shared base URL, query params and JSON fetch
- `web/src/api/dashboard.ts` — `fetchReceiptsByDateRange()`
- `web/src/utils/period.ts` — `computePeriod`, `periodLabel`, `buildMonthLabels`, `MONTH_NAMES`
- `web/src/utils/chart.ts` — `yAxisTicks`, `xTickLabel`
- `web/src/utils/format.ts` — `text`, `euro`, `quantity`, `retailerLabel`, `addressText`
- `web/src/types/dashboard.ts` — typed section rows and receipts
- `web/package.json` — depends on `echarts` and `vue-echarts`
- `web/vite.config.ts` — Vite+ config (lint/fmt/typecheck, `typecheck` task)
- `web/pnpm-workspace.yaml` — Vite+ catalog for `vite`, `vitest`, `vite-plus`
- `web/src/env.d.ts` — `*.vue` module shim for tsgo
- `pyproject.toml` and `uv.lock`
- `api/server.py`
- `web/src/components/__tests__/TrendECharts.spec.ts` — SVG trend chart and interaction tests
- `web/src/components/__tests__/ReceiptListModal.spec.ts`
- `web/src/components/__tests__/DashboardPanels.spec.ts` — dashboard panel rendering and summary tests
- `tests/test_api_receipts.py` — by-date endpoint tests
- `tests/test_kpi_dtos.py` — TimeSeriesRow retailers test
- `tests/test_kpi_store.py` — GROUP_CONCAT aggregation test
- `tests/test_dashboard_service.py` — retailers in dashboard payload
