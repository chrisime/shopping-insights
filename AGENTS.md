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
- Dashboard payload serialization is shared between backend and Vue.
- `start_backend.sh` runs the API from the repo venv.
- The Vue app builds and the focused dashboard tests pass.

## Backend
- Start the API with `./start_backend.sh`.
- Use the project venv for Python commands, for example `./.venv/bin/python -m pytest -q`.
- The dashboard API lives at `api/main.py` and includes the `ui`, `kpis`, `receipts`, `items`, `exports`, and `triggers` routers.
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
- `python3 -m pytest -q` passes.
- `corepack pnpm test -- --run src/components/__tests__/DashboardPanels.spec.ts src/components/__tests__/DashboardPage.spec.ts src/components/__tests__/DashboardFilterBar.spec.ts` passes.
- `corepack pnpm build` passes.

## Key Decisions
- Keep backend payloads section-based and reusable.
- Keep empty-database / no-receipts handling in the frontend payload layer.
- Use `shared.retailer_runtime.get_retailer_runtime()` for receipt JSON path resolution.
- Expose dashboard errors as structured payloads with `error_code` and `detail`.

## Relevant Files
- `api/main.py`
- `api/routes/`
- `api/services/`
- `client/lidl_client.py`
- `fetch_tickets.py`
- `workflows/`
- `frontend/dashboard_errors.py`
- `frontend/dashboard_state.py`
- `frontend/ui_model.py`
- `frontend/schema.py`
- `web/src/components/`
- `web/src/types/dashboard.ts`
- `requirements.txt`
- `start_backend.sh`
