# ADR Review Manifest

- Status: completed
- Review date: 2026-11-22

## Review Summary

ADR review completed for this change. The change splits the dashboard KPI
presentation into two sections and adds a Rossmann "Preisvorteil" card. It is a
tactical UI composition change and does not establish a new long-term
architectural commitment, technology, boundary, or external contract.

## In-Force ADRs Reviewed

- `adr/0001-use-sqlalchemy-core-for-persistence.md` — not relevant to dashboard
  presentation.
- `adr/0002-manage-schema-with-alembic.md` — no schema change in this change.
- `adr/0003-workflows-single-import-path.md` — no import-path change.
- `adr/0004-use-builtin-generics-and-union-annotations.md` — no annotation
  policy change.
- `adr/0005-authenticate-dm-via-oauth-pkce.md` — no auth change.
- `adr/0007-authenticate-rossmann-per-import.md` — no auth change; only the
  Rossmann KPI summary card is added.
- `adr/0006-authenticate-rossmann-via-account-api.md` is superseded by 0007 and
  treated as historical context only.

## New Durable ADRs Created

- None — no major durable architectural decisions were introduced. The
  section-based payload contract and presence-gated card rendering follow
  existing patterns and do not warrant a repository-level ADR.
