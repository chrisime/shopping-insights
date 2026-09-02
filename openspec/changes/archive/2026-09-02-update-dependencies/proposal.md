## Why

The project's declared dependencies have drifted from what the code actually uses. Backend `requirements.txt` pins packages that are no longer imported anywhere (`selenium`, `webdriver-manager`, `pandas`, `httpx`) and frontend `web/package.json` still declares the vue-chartjs stack (`chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs`) after the D3 migration. At the same time several packages are pinned several minor/major versions behind the currently installed ones. This accumulates unused install size, stale security surface, and confusing drift between declared and real dependencies.

## What Changes

- Update backend `requirements.txt` to the currently installed, working versions (verified against the project venv and the passing test suite).
- Remove backend packages that are never imported: `selenium`, `webdriver-manager`, `pandas`, `httpx`.
- Update frontend `web/package.json` dependencies to current minor/major versions.
- Remove frontend packages no longer used after the D3 migration: `chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs`; delete the leftover `web/src/chart-plugins/monthHeaderPlugin.ts` (only its `MonthLabel` interface is still referenced) and relocate that interface.
- Regenerate `web/pnpm-lock.yaml` to match.
- Verify: backend test suite (`pytest`), frontend tests (`vitest`), frontend build (`vite build`), and a clean `pip install -r requirements.txt` / `pnpm install` resolve without errors.

## Capabilities

### New Capabilities
- `dependency-hygiene`: The set of declared project dependencies (backend `requirements.txt`, frontend `web/package.json` + lockfile) stays minimal, current, and in sync with what the code actually imports; every removed/updated dependency leaves the test suite and production build green.

### Modified Capabilities
- No existing spec-level behaviour changes.

## Impact

- `requirements.txt` — updated versions; removal of `selenium`, `webdriver-manager`, `pandas`, `httpx`.
- `web/package.json` — updated versions; removal of `chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs`.
- `web/pnpm-lock.yaml` — regenerated.
- `web/src/chart-plugins/monthHeaderPlugin.ts` — deleted; `MonthLabel` interface moves to a shared location.
- `web/src/components/TrendBarChart.vue`, `web/src/components/TrendChartPanel.vue` — import the relocated `MonthLabel` type.
- `web/src/chart-plugins/__tests__/monthHeaderPlugin.spec.ts` — removed with the plugin.
- Verification: `./.venv/bin/python -m pytest -q`, `corepack pnpm test -- --run`, `corepack pnpm build`.