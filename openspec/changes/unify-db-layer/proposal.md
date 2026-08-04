## Why

The persistence layer is inconsistent: `storage/sqlite_domains.py` builds queries via PyPika, while `storage/kpi_store.py` and parts of `storage/sqlite_receipt_store.py` use raw SQL with f-string composition. In addition, the schema/migration runner (`sqlite_migration_runner.py`) is self-written and offers neither down migrations nor autogenerate. This complicates maintenance, makes analytical queries fragile, and blocks clean schema evolution.

## What Changes

- **Single query technology (SQLAlchemy Core):** Replaces PyPika and raw SQL with a single SQLAlchemy-Core-based layer for write and read/analysis paths. **BREAKING:** the PyPika dependency is removed; `pypika>=0.51.1` is dropped from `requirements.txt`.
- **Alembic as the migration system:** Replaces the self-written runner and `V001__core_schema.sql`. **BREAKING:** existing databases are rebuilt — Alembic owns the schema starting from the baseline migration; existing SQLite data is discarded and receipts must be re-imported. Future schema changes run as Alembic migrations (up/down, autogenerate).
- **Centralized connection management:** A single SQLAlchemy `Engine` replaces the repeated `sqlite3.connect` calls in the store functions.
- **Dataclass entities stay:** `sqlite_entities.py` remains the typed projection layer; SQLAlchemy Core results continue to be mapped into these dataclasses.
- **Assumption:** SQLite is the only target; no Postgres port is planned.

## Capabilities

### New Capabilities
- `persistence-query-layer`: Unified SQLAlchemy Core access for writing (domains) and analytical reading (KPIs, receipt queries) including dynamic filters, aggregations, and pagination.
- `schema-migrations`: Alembic-managed schema versioning and migration application with baseline, up/down migrations, and autogenerate support.

### Modified Capabilities
<!-- No existing specs in openspec/specs/ — nothing to modify. -->

## Impact

- `storage/sqlite_domains.py` — rewritten from PyPika to SQLAlchemy Core
- `storage/kpi_store.py` — rewritten from raw SQL to SQLAlchemy Core
- `storage/sqlite_receipt_store.py` — rewritten (including mixed raw-SQL paths)
- `storage/sqlite_migration_runner.py` and `storage/sqlite_migrations/V001__core_schema.sql` — removed
- `storage/sqlite_entities.py` and `sqlite_entity_builders.py` — kept, possibly slightly adjusted
- `requirements.txt` — add `sqlalchemy` + `alembic`, remove `pypika`
- `tests/` — store tests are migrated to the new layer; raw-SQL fixtures (e.g., in `test_kpi_store.py`) are replaced
- Database — existing DBs are discarded; re-import receipts via `fetch_tickets.py` (initial/update flows)
