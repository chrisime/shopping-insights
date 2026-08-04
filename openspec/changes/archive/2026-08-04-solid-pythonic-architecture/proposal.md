# Proposal: solid-pythonic-architecture

## Why

The codebase grew feature-first: several modules mix responsibilities (god modules), the `workflows/` layer carries a two-level template-method + strategy abstraction that two retailers do not justify, and annotations still use pre-3.10 `typing` generics. This change audits every module (except `storage/`, freshly unified in the previous change) and refactors toward SOLID where it reduces real complexity and toward idiomatic Python throughout — without adding abstraction layers.

## What Changes

- **workflows/ de-abstraction**: remove the `ImportPipeline` abstraction layer; fold load → parse → validate → persist into a single shared local-import path used by both retailer workflows. Keep one thin workflow base (or shared functions), not two.
- **No new abstraction**: the refactor must not introduce new ABCs, interfaces, or DI frameworks; SOLID is applied as a lens for real complexity (SRP module splits, DIP via trivial injection where coupling is hidden), not as a mandate for layers.
- **Module responsibilities (SRP)**: split god modules with mixed concerns (e.g. `api/services/dashboard_service.py` mixes models, serializers, metric builders, service) into focused modules/functions across `api/`, `auth/`, `parsing/`, `shared/`.
- **Idiomatic Python**: modernize the ~255 legacy `typing` annotations (`Optional[...]`/`List[...]`/`typing.List` → `X | None`/`list[...]` PEP 585) across all in-scope modules; normalize built-in generics; remove redundant `__all__`/`Any` noise where safe.
- **Behavior preserved**: pure refactor; no API or user-visible behavior change.
- **Excluded**: `storage/` (unified on SQLAlchemy Core in the archived `unify-db-layer` change) and the Vue frontend.

## Capabilities

### New Capabilities
- `workflows-architecture`: The workflow layer keeps a single shared local-import path, carries at most one thin workflow base, and does not add interface-only abstractions.
- `pythonic-code-style`: Annotations use built-in generics (`list[...]`, `dict[...]`, `X | None`) rather than legacy `typing` generics; code avoids non-Pythonic (Java/C#-style) patterns.
- `module-responsibilities`: Modules keep a single clear responsibility; god modules with mixed concerns are decomposed; hidden concrete coupling is reduced without DI frameworks.

### Modified Capabilities
<!-- None: no existing behavior spec (persistence-query-layer, schema-migrations) changes. -->

## Impact

- **Code**: `api/`, `auth/`, `client/`, `config/`, `export/`, `parsing/`, `shared/`, `workflows/`, `fetch_tickets.py`, `result_types.py`.
- **Behavior/API**: none — behavior-preserving refactor.
- **Dependencies**: none added or removed.
- **Verification**: full backend suite (429 tests), frontend suite + build (65 tests), acceptance tests, and pyright clean (0 errors) must stay green; `ImportPipeline` file removed; no new ABCs introduced.
