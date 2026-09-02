## Context

The project has two dependency manifests that have drifted from reality:

- **Backend** `requirements.txt` declares 17 packages. `selenium`, `webdriver-manager`, `pandas`, and `httpx` are not imported by any source module or test (verified with `grep -rl "import <pkg>"` over `api/ auth/ cli/ client/ config/ parsing/ shared/ storage/ workflows/ fetch_tickets.py tests/`). The venv already carries newer versions of the remaining packages (e.g. `fastapi==0.139.0`, `pydantic==2.13.4`, `SQLAlchemy==2.0.51`) than the minimums in `requirements.txt`, and the 602-test suite passes on those installed versions.
- **Frontend** `web/package.json` still declares the vue-chartjs stack (`chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs`) after the D3 migration. `web/src/chart-plugins/monthHeaderPlugin.ts` is the only consumer of `chart.js` and is itself only referenced by its own test and by `TrendBarChart.vue`/`TrendChartPanel.vue` for the `MonthLabel` interface. `chartjs-plugin-datalabels` and `vue-chartjs` have zero imports.

Constraints: use `pnpm` in `web/`, use the project venv (`.venv/`) for backend commands, no new third-party libraries. The dashboard behaviour must not change.

## Goals / Non-Goals

**Goals:**
- Pin `requirements.txt` to the currently installed, test-verified versions.
- Remove backend packages that are never imported: `selenium`, `webdriver-manager`, `pandas`, `httpx`.
- Update `web/package.json` to current minor/major versions of in-use packages.
- Remove the unused frontend chart stack (`chart.js`, `chartjs-plugin-datalabels`, `vue-chartjs`) and delete `monthHeaderPlugin.ts`, relocating its `MonthLabel` interface.
- Regenerate `web/pnpm-lock.yaml`.
- Prove everything still works: backend tests, frontend tests, frontend build, clean installs.

**Non-Goals:**
- Refactoring imports or behaviour beyond relocating the `MonthLabel` type.
- Pinning transitive dependencies or adding a lockfile for the backend.
- Touching the legacy `venv/` directory or `start_backend.sh` runtime (uses its own `venv/bin/python`).
- Changing the OpenSpec config (`openspec/config.yaml` has a pre-existing duplicate `specs:` key that produces a CLI parse warning; out of scope here).

## Decisions

**D1 — Update backend versions to what the venv actually runs.**
`requirements.txt` uses `>=` floors; set each remaining package to the version installed in `.venv` (the venv that runs the passing 602-test suite). This makes the manifest reflect a known-good, tested set rather than stale minimums. Alternative (leaving floors as-is) was rejected because it keeps the drift the change is meant to eliminate.

**D2 — Remove `selenium`, `webdriver-manager`, `pandas`, `httpx` from `requirements.txt`.**
Grep over the full source + test tree shows zero imports of these four packages (browser cookie extraction uses `browser_cookie3` + `requests`, PDFs use `pdfplumber`, data handling uses `simplejson`/`pyarrow`). Removing them shrinks install size and stale security surface. This matches the "no unused dependencies" spec requirement.

**D3 — Remove the frontend chart stack and relocate `MonthLabel`.**
`chart.js`, `chartjs-plugin-datalabels`, and `vue-chartjs` are only reachable through `monthHeaderPlugin.ts`. `TrendBarChart.vue` and `TrendChartPanel.vue` import only the `MonthLabel` interface from it. Plan: move `MonthLabel` into a small shared module (e.g. `web/src/types/chart.ts`), update the two components' imports, delete `monthHeaderPlugin.ts` and its spec. Alternative (keeping `chart.js` only for the type import) was rejected because it leaves a whole unused dependency for a single type that is trivial to relocate.

**D4 — Update frontend versions via pnpm and regenerate the lockfile.**
Run `pnpm install` (or `pnpm update`) so `web/package.json` and `web/pnpm-lock.yaml` move together. `@types/d3` stays because the `d3` package ships no bundled type declarations (verified: `d3/package.json` has no `types` field).

**D5 — Verification order: clean installs first, then tests, then build.**
Run `pip install -r requirements.txt` in a scratch venv, then `.venv` backend tests, then `pnpm install`, frontend tests, frontend build. This proves the declared set resolves and is sufficient.

## Risks / Trade-offs

- [Removing a package that is actually used at runtime through an indirect import] -> Mitigation: grep across source + tests before removal; the full test suite exercises imports, and the API smoke test (`./start_backend.sh` + `curl /ui`) runs after.
- [Version bump to the venv's installed versions hides that the venv is stale] -> Mitigation: versions are taken from the venv that currently passes 602 tests; a clean-install verification confirms the manifest alone reproduces a working env.
- [Relocating `MonthLabel` breaks the two components] -> Mitigation: update both import sites in the same change; frontend tests + build catch any miss.
- [`pnpm` not available via `corepack` on this machine] -> Mitigation: fall back to a direct `pnpm` invocation if installed; lockfile regeneration is deterministic from the manifest.

## Migration Plan

No data migration. Deployment is a source-only change:
1. Edit `requirements.txt` and `web/package.json`.
2. Regenerate `web/pnpm-lock.yaml`.
3. Run the verification suite (clean installs → backend tests → frontend tests → frontend build → API smoke test).
4. Rollback is a git revert of the two manifests + lockfile; no schema or state changes involved.

## Open Questions

- None blocking. Version choice for `web/package.json` will follow the currently resolvable latest compatible versions unless the user prefers specific pins.
- No in-force ADR is revisited by this change (dependency hygiene is orthogonal to ADR-0001…0006).