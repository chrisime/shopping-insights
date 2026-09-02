## 1. Backend dependency hygiene

- [x] 1.1 Confirm unused backend packages with a source-wide grep (exclude `.venv/`/`venv/`): `selenium`, `webdriver-manager`, `pandas`, `httpx` must have zero imports in `api/ auth/ cli/ client/ config/ parsing/ shared/ storage/ workflows/ fetch_tickets.py tests/`.
- [x] 1.2 Update `requirements.txt`: remove `selenium`, `webdriver-manager`, `pandas`, `httpx`.
- [x] 1.3 Update remaining `requirements.txt` entries to the versions currently installed in `.venv/` (the venv the passing test suite runs on), keeping the `>=` floor style.
- [x] 1.4 Verify with a clean install: create a scratch venv, run `pip install -r requirements.txt`, confirm all packages resolve without errors.
- [x] 1.5 Run `./.venv/bin/python -m pytest -q` and confirm the full backend suite (602 tests) passes.

## 2. Frontend dependency hygiene

- [x] 2.1 Confirm unused frontend packages with a source-wide grep: `chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs` must have no imports outside `web/src/chart-plugins/monthHeaderPlugin.ts`.
- [x] 2.2 Move the `MonthLabel` interface from `web/src/chart-plugins/monthHeaderPlugin.ts` to a shared module (e.g. `web/src/types/chart.ts`).
- [x] 2.3 Update `web/src/components/TrendBarChart.vue` and `web/src/components/TrendChartPanel.vue` to import `MonthLabel` from the new location.
- [x] 2.4 Delete `web/src/chart-plugins/monthHeaderPlugin.ts` and `web/src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts`.
- [x] 2.5 Update `web/package.json`: remove `chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs`; bump remaining deps to current compatible versions.
- [x] 2.6 Run `pnpm install` in `web/` to regenerate `web/pnpm-lock.yaml` and confirm no missing/extraneous packages are reported.

## 3. Frontend verification

- [x] 3.1 Run `pnpm test -- --run` in `web/` and confirm all tests pass (66 tests, 16 files baseline).
- [x] 3.2 Run `pnpm build` in `web/` and confirm the production build completes cleanly.
- [x] 3.3 Smoke-test the API with `./start_backend.sh` and `curl http://localhost:8000/ui/dashboard` to confirm runtime health after dependency changes.

## 4. Spec Validation

- [x] 4.1 Run `openspec validate update-dependencies --type change --strict` and fix any spec/scenario issues before archiving.