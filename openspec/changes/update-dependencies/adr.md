# ADR Review Manifest

- Status: completed
- Review date: 2026-09-02

## Review Summary

ADR review completed for this change.

## In-Force ADRs Reviewed

- ADR-0001: Use SQLAlchemy Core for all persistence queries (in force, not superseded).
- ADR-0002: Manage the SQLite schema with Alembic migrations (in force, not superseded).
- ADR-0003: Single shared local-import path with one thin workflow base (in force, not superseded).
- ADR-0004: Use built-in generics and union annotations (in force, not superseded).
- ADR-0005: Authenticate dm via OAuth 2.0 PKCE with session-cookie reuse (in force, not superseded).
- ADR-0006: Authenticate Rossmann digital receipts via the Rossmann account API plus anybill bearer token (in force, not superseded).

## New Durable ADRs Created

- None - dependency hygiene (pinning to tested versions, pruning unused packages, relocating a frontend type) is a tactical maintenance decision that introduces no new architectural commitment and does not diverge from any in-force ADR.