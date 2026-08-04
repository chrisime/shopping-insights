# ADR Review Manifest

- Status: completed
- Review date: 2026-08-04

## Review Summary

ADR review completed for this change.

Two durable architectural decisions were identified in `design.md` and recorded as new repository-level ADRs:

- `workflows/` de-abstraction — single shared local-import path, at most one thin workflow base, no new interface-only abstractions (ADR-0003).
- Annotation modernization — PEP 585 built-in generics and `X | None` unions as the long-term typing convention (ADR-0004).

Tactical items (god-module splits, `__all__`/`Any` cleanup) do not meet the durable-commitment bar and were intentionally not recorded as ADRs.

## In-Force ADRs Reviewed

- ADR-0001 (`adr/0001-use-sqlalchemy-core-for-persistence.md`) — accepted, in force; constrains `storage/` (excluded from this change) and is coherent with it.
- ADR-0002 (`adr/0002-manage-schema-with-alembic.md`) — accepted, in force; constrains `storage/` (excluded from this change) and is coherent with it.
- ADR-0003 (`adr/0003-workflows-single-import-path.md`) — accepted; created by this change, in force.
- ADR-0004 (`adr/0004-use-builtin-generics-and-union-annotations.md`) — accepted; created by this change, in force.

No prior ADR is superseded by this change; the two new ADRs extend, rather than diverge from, the existing in-force set.

## New Durable ADRs Created

- ADR-0003: Single shared local-import path with one thin workflow base — `adr/0003-workflows-single-import-path.md`
- ADR-0004: Use built-in generics and union annotations — `adr/0004-use-builtin-generics-and-union-annotations.md`
