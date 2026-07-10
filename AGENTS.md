## Goal
- Python supermarket-ticket analyzer for Lidl and REWE.
- Downloads receipts, parses HTML/PDF data, normalizes it, stores it in SQLite, and serves KPI data to the Vue dashboard.

## Constraints & Preferences
- Vue is the only dashboard frontend.
- Use `pnpm` in `web/`.
- Use the project venv for backend commands.
- Lidl requests must retry with exponential backoff on 429/5xx.
- Shared auth-method resolution (`--browser` / `--cookies-file`) should stay common between Lidl and REWE.
- No third-party retry libraries; use plain `requests` + `time.sleep`.
- Address extraction should prefer positive validation and shared constants over blacklist heuristics.

## Current State
- Vue dashboard migration is on `main`.
- Streamlit entrypoint, renderer, and tests were removed.
- API routes exist for `ui`, `kpis`, `receipts`, `items`, `exports`, and `triggers`.
- Charts migrated from vue-chartjs (canvas) to D3 (SVG) — `TrendBarChart.vue`.
- Bar hover → CSS darkening + D3 SVG tooltip (period, total, count, avg, retailers).
- Bar click → ReceiptListModal via `GET /receipts/by-date` API.
- Monthly x-axis shows "Jan 2024" format.
- Time-series DTO includes `retailers` field (GROUP_CONCAT in SQL).
- Backend: 424 tests passing. Frontend: 65 tests (17 files) passing, build succeeds.

## Backend
- Start the API with `./start_backend.sh`.
- Use the project venv for Python commands, for example `./.venv/bin/python -m pytest -q`.
- The dashboard API lives at `api/main.py` and includes the `ui`, `kpis`, `receipts`, `items`, `exports`, and `triggers` routers.
- `GET /receipts/by-date` endpoint supports `start_date`, `end_date`, and optional `retailer` filter.
- Time-series KPIs in `storage/kpi_store.py` use `GROUP_CONCAT(DISTINCT s.retailer_code)` for retailer aggregation.
- `shared/kpi_dtos.py` defines `TimeSeriesRow` DTO with `retailers: list[str]`.
- Receipt fetching and parsing are driven by the workflow layer under `workflows/`.
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
- `python3 -m pytest -q` → 424 passed.
- `corepack pnpm test -- --run` → 65 passed (17 files).
- `corepack pnpm build` → builds cleanly.
- `./start_backend.sh` then `curl http://localhost:8000/ui` confirms API responds.

## Key Decisions
- Keep backend payloads section-based and reusable.
- Keep empty-database / no-receipts handling in the frontend payload layer.
- Use `shared.retailer_runtime.get_retailer_runtime()` for receipt JSON path resolution.
- Expose dashboard errors as structured payloads with `error_code` and `detail`.
- Migrated from vue-chartjs to D3 for trend chart (SVG over canvas for tooltip/hover control).
- Tooltip hides with 200ms delay on mouseleave to prevent flicker.
- Tooltip SVG group rendered AFTER bars in paint order for correct z-index.

## Relevant Files
- `api/main.py`
- `api/routes/`
- `api/services/`
- `shared/kpi_dtos.py` — TimeSeriesRow with `retailers` field
- `storage/kpi_store.py` — GROUP_CONCAT in time-series SQL
- `client/lidl_client.py`
- `fetch_tickets.py`
- `workflows/`
- `frontend/dashboard_errors.py`
- `frontend/dashboard_state.py`
- `frontend/ui_model.py`
- `frontend/schema.py`
- `web/src/components/TrendBarChart.vue` — D3 SVG chart with tooltip + hover
- `web/src/components/TrendChartPanel.vue` — emits `select-period` for bar click
- `web/src/components/ReceiptListModal.vue` — period drill-down modal
- `web/src/components/DashboardPage.vue` — orchestrates modal + period state
- `web/src/api/dashboard.ts` — `fetchReceiptsByDateRange()`
- `web/src/types/dashboard.ts`
- `web/package.json` — depends on `d3` + `@types/d3`
- `requirements.txt`
- `start_backend.sh`
- `web/src/components/__tests__/TrendBarChart.spec.ts` — bar chart + tooltip tests
- `web/src/components/__tests__/ReceiptListModal.spec.ts`
- `web/src/components/__tests__/DashboardPanels.spec.ts` — updated for D3 SVG
- `tests/test_api_receipts.py` — by-date endpoint tests
- `tests/test_kpi_dtos.py` — TimeSeriesRow retailers test
- `tests/test_kpi_store.py` — GROUP_CONCAT aggregation test
- `tests/test_dashboard_service.py` — retailers in dashboard payload
