# Design: solid-pythonic-architecture

## Context

The codebase is a Python backend (`api/`, `auth/`, `parsing/`, `shared/`, `workflows/`, `storage/`, plus top-level CLI `fetch_tickets.py`) serving a Vue dashboard. Two in-force ADRs govern persistence (`storage/`): ADR-0001 (SQLAlchemy Core) and ADR-0002 (Alembic). `storage/` was just unified and is **excluded** from this change.

The refactor targets structural and stylistic debt accumulated feature-first:

- `workflows/` carries **two stacked abstractions**: `ImportWorkflow` (template-method base for download → import → summary) and `ImportPipeline` (ABC for parse → validate → persist), each with retailer subclasses. Two retailers do not justify this layering.
- `api/services/dashboard_service.py` (578 lines) mixes DTOs, metric builders, serializers, and the service class.
- `auth/shared_file_auth.py` (311 lines) mixes cookie diagnostics with session construction.
- ~57 files use legacy `typing` generics (`Optional[...]`, `List[...]`, `typing.List`, …) instead of PEP 585 built-ins.

Behavior must be preserved; the full backend suite (429 tests), frontend suite (65) and pyright are the safety net.

## Goals / Non-Goals

**Goals:**
- Reduce `workflows/` to one thin abstraction: keep a single shared local-import path (load → parse → validate → persist) and at most one workflow base.
- Split god modules that mix models, builders, and orchestration into focused units, using plain functions/parameter injection (no DI framework, no new ABCs).
- Modernize annotations to PEP 585/604 across all in-scope modules; drop dead `typing` imports and redundant `__all__`/`Any` noise.
- Preserve every public contract used by `fetch_tickets.py` (`run_lidl_initial`, `run_lidl_update`, `run_rewe_initial`, `run_rewe_update`) and the API routers.
- Keep `storage/` untouched (freshly unified; ADR-0001/0002 in force).

**Non-Goals:**
- No behavior or API contract changes.
- No new dependencies, no lint/format tooling migration (no ruff/black/etc.).
- No performance work, no new test coverage beyond what proves the refactor.
- No changes to the Vue frontend.
- No reintroduction of the ORM or PyPika.

## Decisions

### Decision 1: Collapse `ImportPipeline` into a single shared local-import function

Remove `workflows/import_pipeline.py` and its `ImportPipeline` ABC. Fold its `run()` orchestration (load → `parse_receipts` → `validate_receipts` → `receipt_dict_to_dto` → `store.persist_receipts` → skipped-report + printing) into one shared function, e.g. `import_local_sources()` in a new `workflows/local_import.py`.

Retailer-specific behavior currently supplied via subclass attributes/hooks becomes plain parameters:
- `load_payload` → a `loader: Callable[[Path], Any]` argument (Lidl passes a JSON→`LidlTicketDTO` loader; REWE passes the identity path loader).
- `detail_key`, `load_error_reason_kind`, `retailer_display_name`, `_skipped_report_filename` → parameters or a small data record.
- Skipped-report writing/printing → the existing shared reporting helpers, called from the shared function.

**Rationale:** The ABC contributes only a handful of configurable values and one hook; a function with a loader callable and a config record expresses the same variation with less indirection. "Why over X": keeping the ABC adds an inheritance tier that two concrete subclasses do not justify (per the de-abstraction goal); making it a plain function keeps the stage pipeline (`pipeline_runner.py`) unchanged while removing the second abstraction level.

**Alternative considered:** Keep `ImportPipeline` but merge it into `ImportWorkflow`. Rejected: that re-attaches import to the download lifecycle and still leaves a two-tier structure.

### Decision 2: Keep exactly one thin base — `ImportWorkflow` — and remove its abstract surface

`ImportWorkflow` stays as the single workflow base driving `run_initial`/`run_update` (download → import → summary), because both retailers genuinely share that control flow. The retailer subclasses remain concrete, thin, and parameter-carrying (session/auth config via constructor).

The `_run_local_import` abstract hook now calls the shared `import_local_sources()` (Decision 1) instead of constructing an `ImportPipeline` subclass.

**Rationale:** The proposal allows one thin base; the download-then-import lifecycle is the one real shared behavior. No new ABCs are introduced anywhere (existing base retained, second base removed).

**Alternative considered:** Flatten `ImportWorkflow` to standalone functions too. Rejected for now — it would force `fetch_tickets.py` callers to re-express shared run_initial/run_update sequencing; deferred as a later refactor if the base becomes trivially thin.

### Decision 3: Split god modules by responsibility, not by layer

Split only modules where mixed concerns create real friction, using the same decomposition criteria (single clear responsibility per unit; plain function/data records over service classes where behavior is stateless).

- `api/services/dashboard_service.py` (578 L) → three focused units:
  - `api/services/dashboard_models.py` — DTOs/dataclasses (`DashboardState`, `DashboardPageModel`, `DashboardDerivedMetrics`, `VueDashboardPayload`, …).
  - `api/services/dashboard_builders.py` — pure builders (`_build_derived_metrics`, `_build_time_series`, `_build_top_items`, `_build_kpi_metrics`, `build_dashboard_state`, `build_dashboard_page_model`).
  - `api/services/dashboard_service.py` — thin `DashboardService` (empty-state handling + payload construction) importing the builders/models.
  - `DashboardError` stays in `api/services/dashboard_errors.py` (already separate).
- `auth/shared_file_auth.py` (311 L) → two units:
  - cookie diagnostics (`assess_cookie_quality`, `print_cookie_diagnostics`, `_build_next_steps`, `CookieDiagnosticProfile`, …) → e.g. `auth/cookie_diagnostics.py`.
  - session construction from cookies (`build_cookie_session`, `_prepare_cookie_dicts`, `_store_cookies_in_session`, …) → remains as the file-auth entry point.
- Other large modules (`shared/receipt_schema.py` 341 L, `auth/session_cookie_recovery.py` 262 L, `shared/receipt_dto.py` 243 L) are **evaluated** during the audit with the same criteria; split only if they actually mix unrelated concerns. The audit findings are recorded in this design's appendix to be expanded during implementation.

**Rationale:** SRP via decomposition of real mixed concerns, not mechanical per-file splitting. "Why not service-per-class everywhere": many functions are stateless; plain functions with explicit params are more Pythonic and match the "no DI framework" constraint.

**Alternative considered:** Introduce interfaces/repositories for the API layer. Rejected: adds abstractions without pulling weight; DIP is served by parameter injection where coupling is hidden.

### Decision 4: Modernize annotations to PEP 585/604 in one sweep

Across all in-scope modules (`api/`, `auth/`, `client/`, `config/`, `export/`, `parsing/`, `shared/`, `workflows/`, `fetch_tickets.py`, `result_types.py`):

- `Optional[X]` → `X | None`; `List[X]` → `list[X]`; `Dict[X, Y]` → `dict[X, Y]`; `Tuple`/`Set`/`Mapping`/`Iterable`/`Sequence`/`Callable` → built-in/`collections.abc` equivalents.
- Remove `typing` imports that become unused; keep `Callable`/`TypeVar`/`Any` only where genuinely needed (e.g. `pipeline_runner.py` `TypeVar`).
- Keep `from __future__ import annotations` where already present; add only where a name must stay deferred (string forward refs). Since the runtime is Python 3.12/3.14, `X | None` and built-in generics evaluate at runtime safely.

**Rationale:** PEP 585/604 is the modern idiomatic form and is runtime-safe on 3.12+. "Why not run a codemod tool": no new tooling per Non-Goals; a mechanical in-repo pass is reviewable and test-covered by the existing suite.

**Alternative considered:** Leave annotations untouched. Rejected: it is an explicit goal, low-risk, and high-surface cleanup.

### Decision 5: Remove redundant `__all__`/`Any` noise where safe

Where a module's `__all__` merely mirrors its public functions (e.g. `workflows/lidl_workflow.py`, `workflows/rewe_workflow.py`), keep it only if it genuinely gates the public surface (the CLI imports `run_lidl_*`/`run_rewe_*` — those stay exported regardless). Drop `Any` where a more precise type is trivial. No mass removal; judged per module.

## Current vs Target (lightweight C4 component view)

**workflows/ — current**

```text
fetch_tickets.py (CLI)
   |  run_lidl_initial / run_lidl_update / run_rewe_initial / run_rewe_update
   v
+--------------------------- workflows/ ---------------------------+
|                                                                  |
|  ImportWorkflow (ABC)  <---- _LidlImportWorkflow, _ReweImportWorkflow |
|    | run_initial / run_update (template-method)                  |
|    v                                                             |
|  ImportPipeline (ABC)  <---- _LidlImportPipeline, _ReweImportPipeline |
|    | run() -> parse/validate/persist orchestration               |
|    v                                                             |
|  pipeline_runner.py (parse_receipts / validate_receipts)         |
|  pipeline_types.py (records/issues/result DTOs)                  |
+-----------------------------------------------------------------+
   | persist
   v
storage/ (ReceiptStore)          parsing/ (lidl_receipt_parser, rewe_ebons_parser, …)
```

**workflows/ — target**

```text
fetch_tickets.py (CLI)
   |  run_lidl_initial / run_lidl_update / run_rewe_initial / run_rewe_update
   v
+--------------------------- workflows/ ---------------------------+
|                                                                  |
|  ImportWorkflow (one thin base)  <---- _LidlImportWorkflow,       |
|    | run_initial / run_update                                    | _ReweImportWorkflow
|    v                                                             |
|  local_import.py: import_local_sources(...)  (single shared path)|
|    | loader: Callable[[Path], Any]  (Lidl JSON loader / REWE path)|
|    v                                                             |
|  pipeline_runner.py (parse_receipts / validate_receipts)         |
|  pipeline_types.py (records/issues/result DTOs)                  |
+-----------------------------------------------------------------+
   | persist
   v
storage/ (ReceiptStore)          parsing/ (lidl_receipt_parser, rewe_ebons_parser, …)
```

**api/services/ — current vs target (SRP split)**

```text
current:  dashboard_service.py [DTOs + builders + service]   shared_file_auth.py [diagnostics + session building]
            |  (578 lines, mixed)                                 |  (311 lines, mixed)
target:   dashboard_models.py   (DTOs)
          dashboard_builders.py (pure builders)               cookie_diagnostics.py (assessment/printing)
          dashboard_service.py  (thin service)                shared_file_auth.py  (session construction)
```

## Risks / Trade-offs

- **Behavior drift during split** → [Mitigation] Each split is a pure move + import rewrite; full backend suite (429) and pyright must pass after every commit; the API and CLI contracts are covered by `tests/test_api_*` and workflow tests.
- **`from __future__ import annotations` + runtime generics on 3.12** → [Mitigation] Built-in generics and `X | None` evaluate fine at runtime on 3.12/3.14; no 3.9 support exists, so no compatibility concern.
- **`Callable`/`TypeVar` imports becoming "unused" after modernization** → [Mitigation] pyright + the suite catch accidental removal; keep annotations honest rather than forcing `# noqa`.
- **De-abstraction breaks `fetch_tickets.py` or the API** → [Mitigation] `run_lidl_*`/`run_rewe_*` signatures stay identical; `import_local_sources` keeps the same stage pipeline and DTO types, so callers are unaffected.
- **Scope creep into `storage/`** → [Mitigation] Explicit Non-Goal; ADR-0001/0002 remain in force; no storage file is edited.

## Migration Plan

Pure refactor; no data migration and no rollout beyond the code change.

1. Commit-by-commit, each green: annotation modernization (Decision 4/5) per package, then `workflows/` de-abstraction (Decisions 1–2), then god-module splits (Decision 3).
2. After each commit run `./.venv/bin/python -m pytest -q` and pyright; frontend suite/build stays untouched (no Vue changes).
3. Rollback = revert the offending commit; since behavior is preserved, no DB or API compatibility concerns.
4. Update `AGENTS.md` "Relevant Files" and the change archive only at completion (archive step).

## Open Questions

- **In-force ADR revision?** None. ADR-0001/0002 concern `storage/` only and are untouched; this change does not supersede them.
- **Exact split of `auth/shared_file_auth.py`** — confirm whether diagnostics helpers are imported by other auth modules (`rewe_file_auth.py`, `lidl_file_auth.py`) before moving; the audit in the apply phase resolves this. If cross-module imports make the split high-churn for low gain, keep `shared_file_auth.py` intact and document the finding instead. **Resolved during apply (task 3.2):** cross-module imports existed but the split was a clean move; `cookie_diagnostics.py` created and imports updated.
- **Whether `workflows/export_workflow.py` and `workflows/error_mapping.py` are already clean** — they are out of the de-abstraction target; audit decides if they need any change.

## Appendix — Audit notes (expanded during implementation)

Initial scan of in-scope modules (line counts from the audit):

- api/ 23 files / 1605 L — god module: `services/dashboard_service.py` (578 L).
- auth/ 12 files / 1821 L — candidate: `shared_file_auth.py` (311 L).
- parsing/ 17 files / 1629 L — large files `shared/receipt_schema.py` (341 L, shared/), `auth/session_cookie_recovery.py` (262 L).
- 57 files contain legacy `typing` generics → Decision 4 sweep.
- ABCs exist only in `workflows/import_pipeline.py` and `workflows/import_workflow.py` → Decision 1/2.

### Audit outcome (task 3.3, apply phase)

- `shared/receipt_schema.py` (341 L) — **no split.** Single responsibility: normalizing raw receipt dicts into the shared schema. The private money/quantity parsers (`_normalize_money_value`, `_parse_numeric_value`) are only used here; the length is dense, related helpers, not mixed concerns.
- `auth/session_cookie_recovery.py` (262 L) — **no split.** Single responsibility: recovering session cookies from Firefox/LibreWolf `recovery.jsonlz4`. Profile discovery, mozLz4 decoding, cookie matching and the privacy-level check all serve that one concern.
- `shared/receipt_dto.py` (243 L) — **no split.** Single responsibility: typed DTOs plus dict↔DTO mapping helpers for normalized receipts; conversion helpers are private and cohesive.
- `auth/shared_file_auth.py` — **split done (task 3.2).** Diagnostics helpers were indeed imported cross-module (`rewe_file_auth.py`/`lidl_file_auth.py` import the profile/assessment/printing helpers; `browser_auth_base.py` imports `analyze_cookie_names`), but the split was a clean pure move + import rewrite (7 symbols → `auth/cookie_diagnostics.py`), not high-churn. Full suite 429 passed after the move.

### pyright verification (task 4.2)

Scope run across `api/ auth/ client/ config/ export/ parsing/ shared/ workflows/ result_types.py fetch_tickets.py` reports **32 errors, all pre-existing and byte-identical to the pre-change baseline** (baseline established in task 1.8 via `git stash` + diff). Every remaining error is in a file this change left untouched or only annotation-rewrote (1:1 line rewrites with no structural change); `shared/receipt_store.py` has no diff at all. The modules this change structurally restructured — `workflows/` (de-abstraction), `api/services/dashboard_*` (split), `auth/cookie_diagnostics.py`/`auth/shared_file_auth.py` (split) — are **0 errors**. The residual 32 are pre-existing technical debt outside this change's scope (notably `api/services/kpi_service.py` passing `limit=` where the store expects `page`/`page_size`, and property-override redeclarations in `rewe_browser_auth.py`); fixing them is deferred as agreed ("other refactorings will come later if necessary").
