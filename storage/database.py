"""Central SQLite engine, connection management and Alembic startup migration."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import Connection, Engine, create_engine, event, pool

from config import storage_config

_ENGINE_CACHE: dict[str, Engine] = {}
ALEMBIC_DIR = Path(__file__).with_name("alembic")
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def _database_path() -> Path:
    return Path(storage_config.SQLITE_RECEIPTS_DB_FILE)


def _database_url() -> str:
    return f"sqlite:///{_database_path()}"


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_DIR))
    command.upgrade(cfg, "head")


def _enable_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


def get_engine() -> Engine:
    """Return a lazily created, per-path cached Engine for the configured database.

    The Engine is cached by the configured database path, so tests that patch
    ``storage_config.SQLITE_RECEIPTS_DB_FILE`` transparently get their own engine.
    """
    db_path = _database_path()
    key = str(db_path)
    engine = _ENGINE_CACHE.get(key)
    if engine is None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(
            _database_url(),
            connect_args={"check_same_thread": False},
            poolclass=pool.NullPool,
        )
        event.listen(engine, "connect", _enable_foreign_keys)
        _run_migrations()
        _ENGINE_CACHE[key] = engine
    return engine


def reset_engine_cache() -> None:
    """Drop cached engines. Used by tests to force a fresh engine per path."""
    _ENGINE_CACHE.clear()


@contextmanager
def connect() -> Iterator[Connection]:
    """Yield a checked-out SQLAlchemy ``Connection`` from the configured engine.

    Callers performing writes must commit explicitly (for example via
    ``engine.begin()``) or the transaction is rolled back on close.
    """
    engine = get_engine()
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()
