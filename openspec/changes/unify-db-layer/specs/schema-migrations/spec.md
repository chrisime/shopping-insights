## ADDED Requirements

### Requirement: The schema is initialized through Alembic migrations

Rule: A fresh database MUST receive the full schema through the Alembic baseline migration on first access.

#### Scenario: A fresh database is created with the baseline schema

- **GIVEN** a database that has not been initialized yet
- **WHEN** the persistence layer opens a connection for the first time
- **THEN** the full database schema is applied through the Alembic baseline migration
- **AND** the migration state is recorded as current

### Requirement: Pending migrations are applied at startup

Rule: Alembic MUST apply pending migrations in version order when the database is opened.

#### Scenario: Multiple pending migrations are applied

- **GIVEN** a database whose schema state is older than the newest migration state
- **WHEN** the persistence layer opens the connection
- **THEN** all pending migrations are applied in version order

### Requirement: Migrations are reversible

Rule: Each migration MUST have a down migration that reverts the schema to the previous state.

#### Scenario: A migration is rolled back

- **GIVEN** a database on which a migration has been applied
- **WHEN** the migration is rolled back
- **THEN** the schema is reverted to the previous state

### Requirement: Schema changes are captured as migrations

Rule: New schema changes MUST be generated as migrations with Alembic instead of being implemented manually.

#### Scenario: A schema change is generated as a migration

- **GIVEN** the data model has changed
- **WHEN** the change is generated as a migration
- **THEN** a new migration with up and down steps is created

### Requirement: The self-written migration system is retired

Rule: The custom migration runner and the legacy SQL migration scripts MUST be removed; existing databases are rebuilt.

#### Scenario: Legacy migration artifacts are removed

- **GIVEN** the project uses Alembic for schema management
- **THEN** the custom migration runner and the legacy SQL migration scripts no longer exist
- **AND** existing databases are rebuilt and receipts are re-imported
