"""Alembic environment wired to the Core metadata and the configured SQLite file.

The database URL is resolved dynamically from
``config.storage_config.SQLITE_RECEIPTS_DB_FILE`` so that tests which patch the
config value run migrations against their temporary database.
"""

from __future__ import annotations

from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine

from config import storage_config
from storage.sqlite_schema import metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = metadata


def _database_url() -> str:
    db_path = Path(storage_config.SQLITE_RECEIPTS_DB_FILE)
    return f"sqlite:///{db_path}"


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(_database_url(), connect_args={"check_same_thread": False})
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
