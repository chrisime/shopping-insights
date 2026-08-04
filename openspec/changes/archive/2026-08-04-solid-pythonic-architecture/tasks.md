# Tasks: solid-pythonic-architecture

## 1. Annotation Modernization (PEP 585/604)

- [x] 1.1 Modernize annotations in `api/` (and `api/services/`): `Optional[X]` → `X | None`, `List[X]` → `list[X]`, `Dict[X, Y]` → `dict[X, Y]`, `typing.X` → built-in; drop now-unused `typing` imports; verify with `./.venv/bin/python -m pytest -q` and pyright.
- [x] 1.2 Modernize annotations in `auth/`, keeping `Callable`/`TypeVar`/`Any` only where genuinely needed.
- [x] 1.3 Modernize annotations in `parsing/`.
- [x] 1.4 Modernize annotations in `shared/`.
- [x] 1.5 Modernize annotations in `client/`, `config/`, `export/`, and `result_types.py`.
- [x] 1.6 Modernize annotations in `workflows/` and `fetch_tickets.py`; keep `from __future__ import annotations` where already present and add only where a deferred name is required.
- [x] 1.7 Remove redundant `__all__`/`Any` noise where safe (judged per module; keep `__all__` that gates the CLI-facing surface `run_lidl_*`/`run_rewe_*`).
- [x] 1.8 Full backend suite (`./.venv/bin/python -m pytest -q`) green and pyright 0 errors after the sweep.

## 2. Workflows De-Abstraction

- [x] 2.1 Create `workflows/local_import.py` with `import_local_sources()`: fold load → `parse_receipts` → `validate_receipts` → `receipt_dict_to_dto` → `store.persist_receipts` → skipped-report + printing into one shared function.
- [x] 2.2 Model retailer-specific variation as parameters: `loader: Callable[[Path], Any]`, `detail_key`, `load_error_reason_kind`, `retailer_display_name`, skipped-report filename.
- [x] 2.3 Update `workflows/import_workflow.py`: `_run_local_import` abstract hook now calls `import_local_sources()`; remove the `ImportPipeline` import.
- [x] 2.4 Update `workflows/lidl_workflow.py`: `_LidlImportPipeline` loader becomes a module-level loader callable (JSON → `LidlTicketDTO`) passed to `import_local_sources()`.
- [x] 2.5 Update `workflows/rewe_workflow.py`: path loader used; remove `_ReweImportPipeline`.
- [x] 2.6 Delete `workflows/import_pipeline.py` and update all imports; ensure `run_lidl_initial`/`run_lidl_update`/`run_rewe_initial`/`run_rewe_update` signatures are unchanged.
- [x] 2.7 Verify: no new ABCs/DI anywhere; `workflows/` has exactly one thin base (`ImportWorkflow`); full backend suite + pyright green.

## 3. Module Responsibilities (SRP)

- [x] 3.1 Split `api/services/dashboard_service.py` (578 L): DTOs → `api/services/dashboard_models.py`; pure builders → `api/services/dashboard_builders.py`; thin `DashboardService` stays in `dashboard_service.py`; `DashboardError` stays in `dashboard_errors.py`.
- [x] 3.2 Split `auth/shared_file_auth.py` (311 L): cookie diagnostics → `auth/cookie_diagnostics.py`; session construction stays as the file-auth entry point; update imports across `auth/` and `api/`.
- [x] 3.3 Audit other large modules (`shared/receipt_schema.py` 341 L, `auth/session_cookie_recovery.py` 262 L, `shared/receipt_dto.py` 243 L): record findings; split only if they genuinely mix unrelated concerns, otherwise document the decision.
- [x] 3.4 Full backend suite + pyright green after each split; no behavior/API contract change.

## 4. Final Verification

- [x] 4.1 Run full backend suite (`./.venv/bin/python -m pytest -q`, expected 429) and frontend suite + build (`corepack pnpm test -- --run`, `corepack pnpm build`).
- [x] 4.2 Run pyright: 0 errors on all changed modules.
- [x] 4.3 Run `openspec validate solid-pythonic-architecture --type change --strict`.
- [x] 4.4 Update `AGENTS.md` "Relevant Files" if module paths changed.
