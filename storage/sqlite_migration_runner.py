"""Führt SQL-Migrationsskripte für den SQLite-Store bei jedem Start nach Bedarf aus."""

from __future__ import annotations

import sqlite3
from pathlib import Path


MIGRATIONS_DIR = Path(__file__).with_name("sqlite_migrations")
MIGRATION_TABLE_SQL = """
create table if not exists schema_migration (
    version text primary key,
    script_name text not null,
    applied_at text not null default current_timestamp
);
""".strip()



def apply_sqlite_migrations(connection: sqlite3.Connection) -> None:
    """Apply all pending SQL migration files in version order."""
    connection.execute(MIGRATION_TABLE_SQL)
    applied_versions = _load_applied_migration_versions(connection)

    for migration_file in _list_migration_files():
        version = migration_file.name.split("__", 1)[0]
        if version in applied_versions:
            continue
        _apply_migration(connection, migration_file, version)
        applied_versions.add(version)



def _load_applied_migration_versions(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("select version from schema_migration").fetchall()
    return {str(row[0]) for row in rows}



def _list_migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(path for path in MIGRATIONS_DIR.glob("V*.sql") if path.is_file())


def _apply_migration(connection: sqlite3.Connection, migration_file: Path, version: str) -> None:
    sql = migration_file.read_text(encoding="utf-8").strip()
    if not sql:
        return

    connection.executescript(sql)

    connection.execute(
        """
        insert into schema_migration (version, script_name)
        values (?, ?)
        """,
        (version, migration_file.name),
    )
