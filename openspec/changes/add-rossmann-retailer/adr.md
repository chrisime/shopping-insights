# ADR Review Manifest

- Status: completed
- Review date: 2026-09-01

## Review Summary

ADR review completed for this change.

## In-Force ADRs Reviewed

- ADR-0001: Use SQLAlchemy Core for all persistence queries (in force, not superseded).
- ADR-0002: Manage the SQLite schema with Alembic migrations (in force, not superseded).
- ADR-0003: Single shared local-import path with one thin workflow base (in force, not superseded) — Rossmann onboarding follows its stated intent (shared import path, no new abstraction tier).
- ADR-0004: Use built-in generics and union annotations (in force, not superseded).
- ADR-0005: Authenticate dm via OAuth 2.0 PKCE with session-cookie reuse (in force, not superseded) — the token-mint-from-session pattern carries over to Rossmann, but the concrete mechanism differs (account API vs OAuth PKCE), so a new ADR is warranted.

## New Durable ADRs Created

- ADR-0006: Authenticate Rossmann digital receipts via the Rossmann account API plus anybill bearer token — records the Rossmann token-mint approach (account.ws login + receipt/auth, `Account-Hash` header, anybill Bearer token, `--browser`/`--cookies-file` reuse, plain-`requests`). See `adr/0006-authenticate-rossmann-via-account-api.md`.