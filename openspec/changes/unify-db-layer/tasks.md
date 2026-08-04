## 1. Dependencies and infrastructure

- [ ] 1.1 Add `sqlalchemy>=2.0` and `alembic>=1.13` to `requirements.txt`; remove `pypika`
- [ ] 1.2 Create `storage/sqlite_schema.py` with Core `MetaData` + `Table` definitions mirroring `V001__core_schema.sql` (retailer, store, purchase, purchase_item, payment_method, purchase_lidl, purchase_rewe, indexes, unique constraints)
- [ ] 1.3 Create `storage/database.py` with a lazily-created `Engine` from `config.storage_config.SQLITE_RECEIPTS_DB_FILE`, a `connect()` context manager, a `PRAGMA foreign_keys = ON` connect-event listener, and startup `alembic upgrade head`
- [ ] 1.4 Set up the Alembic environment (`alembic.ini`, `env.py` wired to metadata + engine URL, `script.py.mako`, `versions/`)
- [ ] 1.5 Generate baseline migration `0001_initial_schema` (up: create schema; down: drop) and verify a fresh database initializes via `alembic upgrade head`

## 2. Write path (domains)

- [ ] 2.1 Port `storage/sqlite_domains.py` from PyPika to SQLAlchemy Core, preserving every method signature and using Core `Table` objects with parameterized `select`/`insert`/`update`
- [ ] 2.2 Add per-domain row-mapping helpers that convert Core `RowMapping` results into the existing dataclass entities with the current `None`/`float`/`str` handling
- [ ] 2.3 Convert the stray raw-SQL query in `PurchaseItemDomain.find_purchase_ids_by_item_name` to Core
- [ ] 2.4 Update `storage/sqlite_receipt_store.py` to obtain connections from `database.py`; convert the raw `DELETE` and dynamic `SELECT` statements to Core
- [ ] 2.5 Keep the explicit `_delete_purchase_children` deletes on the update path (no `INSERT OR REPLACE`)

## 3. Analysis path (KPIs)

- [ ] 3.1 Port `storage/kpi_store.py` to Core: dynamic `.where()` filters instead of `WHERE 1=1` f-string composition, `func.date`/`func.strftime`/`func.group_concat` aggregations, pagination via `.limit()`/`.offset()`
- [ ] 3.2 Preserve exact behaviours: `GROUP_CONCAT(DISTINCT retailer_code)`, weekday remap, Pfand exclusion, and ordering

## 4. Migrations and removal

- [ ] 4.1 Delete `storage/sqlite_migration_runner.py` and `storage/sqlite_migrations/V001__core_schema.sql`
- [ ] 4.2 Remove `pypika` from `requirements.txt` and remove all remaining `pypika` imports
- [ ] 4.3 Add a startup-migration test covering a fresh DB (full schema applied) and an Alembic downgrade

## 5. Tests

- [ ] 5.1 Migrate storage tests to an in-memory SQLite engine with the schema applied via Alembic head; replace raw-SQL fixtures in `tests/test_kpi_store.py` and `tests/test_receipt_store.py`
- [ ] 5.2 Add Alembic migration tests: baseline on a fresh DB, ordered application of pending migrations, and downgrade
- [ ] 5.3 Run the full backend suite `./.venv/bin/python -m pytest -q` and confirm all tests pass

## 6. Data reset and verification

- [ ] 6.1 Delete the existing `shopping_receipts.sqlite` and re-import receipts via the `fetch_tickets.py` initial/update flows
- [ ] 6.2 Smoke-check the dashboard: `./start_backend.sh` then `curl http://localhost:8000/ui`
- [ ] 6.3 Run `openspec validate unify-db-layer --type change --strict` before archive
