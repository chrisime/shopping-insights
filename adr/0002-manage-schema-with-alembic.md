# ADR-0002: Manage the SQLite schema with Alembic migrations

## Status

Accepted

## Date

2026-08-04

## Context and Problem Statement

Schema evolution is handled by a self-written runner (`storage/sqlite_migration_runner.py`) that reads `V*.sql` files, tracks versions in a `schema_migration` table, and offers neither down migrations nor autogenerate. This blocks safe, reviewable schema changes. The project needs a mature migration system that owns the schema going forward.

## Considered Options

- Alembic with a baseline migration applied at startup
- Keep the custom migration runner and extend it
- Manage schema via SQLAlchemy `create_all` only

## Decision Outcome

Chosen option: "Alembic with a baseline migration applied at startup", because Alembic is the de-facto standard for SQLAlchemy-backed migrations, supports ordered up/down migrations and `--autogenerate`, and integrates with the Core metadata. `storage/database.py` runs `alembic upgrade head` on engine creation so fresh databases are fully initialized and existing ones get pending migrations applied in order. Because existing databases were created by the legacy runner, the decision is a fresh rebuild: the baseline migration recreates the current schema, existing SQLite data is discarded, and receipts are re-imported.

### Consequences

- Good, because schema changes become versioned, reversible, and autogeneratable, and the legacy runner and `schema_migration` table are removed.
- Good, because startup applies pending migrations automatically.
- Bad, because existing databases are invalidated by the rebuild and receipts must be re-imported (the receipt JSON sources remain the source of truth).
- Bad, because a new dependency (`alembic>=1.13`) and Alembic setup (`env.py`, baseline revision) are required.
