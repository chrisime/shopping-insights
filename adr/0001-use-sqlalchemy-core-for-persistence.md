# ADR-0001: Use SQLAlchemy Core for all persistence queries

## Status

Accepted

## Date

2026-08-04

## Context and Problem Statement

The persistence layer mixes two query styles inside the same module family: `storage/sqlite_domains.py` builds entity queries with PyPika, while `storage/kpi_store.py` and parts of `storage/sqlite_receipt_store.py` compose raw SQL strings with f-strings and `WHERE 1=1` clause accumulation. This inconsistency makes maintenance harder and analytical queries fragile. The project needs one query technology that serves both the write path and powerful analytical reads (dynamic filters, aggregations, pagination) without a full ORM.

## Considered Options

- SQLAlchemy Core (expression-based query builder)
- Full SQLAlchemy ORM
- SQLModel
- Raw SQL everywhere
- Keep PyPika

## Decision Outcome

Chosen option: "SQLAlchemy Core", because it provides composable, parameterized expressions for the analytical KPI queries (dynamic `WHERE`, `GROUP BY`, SQLite functions via `func`, `LIMIT/OFFSET`) without string composition, and it keeps the existing dataclass entity layer intact (Core rows map into typed dataclasses). The full ORM would add unit-of-work machinery that fights the hand-managed schema; SQLModel couples models to Pydantic and the API layer; raw SQL does not remove the f-string fragility; PyPika has no migration ecosystem and weaker analytical expressiveness.

### Consequences

- Good, because all read and write paths use one consistent, testable query technology and the existing dataclass projection and public store interfaces stay unchanged.
- Good, because queries become parameterized and composable instead of f-string composed.
- Bad, because a new dependency (`sqlalchemy>=2.0`) and a full porting effort are required; SQLite-specific SQL functions are still used, so the layer is not portable to another dialect.
