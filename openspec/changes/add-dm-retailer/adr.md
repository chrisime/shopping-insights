# ADR Review Manifest

- Status: completed
- Review date: 2026-08-31

## Review Summary

ADR review completed for this change.

## In-Force ADRs Reviewed

- ADR-0001: Use SQLAlchemy Core for all persistence queries (in force, not superseded).
- ADR-0002: Manage the SQLite schema with Alembic migrations (in force, not superseded).
- ADR-0003: Single shared local-import path with one thin workflow base (in force, not superseded) — dm onboarding follows its stated intent (shared import path, no new abstraction tier).
- ADR-0004: Use built-in generics and union annotations (in force, not superseded).

## New Durable ADRs Created

- ADR-0005: Authenticate dm via OAuth 2.0 PKCE with session-cookie reuse — records the dm token-acquisition approach (PKCE against `signin.dm.de`, reuse of the shared `--browser` / `--cookies-file` auth-method resolution, plain-`requests` constraint). See `adr/0005-authenticate-dm-via-oauth-pkce.md`.