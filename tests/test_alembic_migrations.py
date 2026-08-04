import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from alembic import command
from alembic.config import Config

from config import storage_config
from storage.database import (
    ALEMBIC_DIR,
    ALEMBIC_INI,
    get_engine,
    reset_engine_cache,
)

EXPECTED_TABLES = {
    "alembic_version",
    "retailer",
    "store",
    "purchase",
    "purchase_item",
    "payment_method",
    "purchase_lidl",
    "purchase_rewe",
}


class AlembicMigrationTests(unittest.TestCase):
    def isolated_db_path(self) -> Path:
        tmp_dir = self.enterContext(tempfile.TemporaryDirectory())
        return Path(tmp_dir) / "receipts.sqlite"

    def setUp(self):
        reset_engine_cache()
        self.db_path = self.isolated_db_path()
        self.enterContext(patch.object(storage_config, "SQLITE_RECEIPTS_DB_FILE", str(self.db_path)))

    def table_names(self) -> set[str]:
        engine = get_engine()
        with engine.connect() as connection:
            rows = connection.exec_driver_sql(
                "select name from sqlite_master where type = 'table'"
            ).fetchall()
        return {row[0] for row in rows}

    def current_alembic_version(self) -> str:
        engine = get_engine()
        with engine.connect() as connection:
            row = connection.exec_driver_sql("select version_num from alembic_version").fetchone()
        assert row is not None
        return str(row[0])

    def _alembic_config(self) -> Config:
        cfg = Config(str(ALEMBIC_INI))
        cfg.set_main_option("script_location", str(ALEMBIC_DIR))
        return cfg

    def test_fresh_database_gets_full_schema_via_baseline_migration(self):
        get_engine()

        self.assertEqual(
            self.table_names(),
            EXPECTED_TABLES,
        )
        self.assertEqual(self.current_alembic_version(), "0001_initial_schema")

    def test_migrations_run_once_for_cached_engine(self):
        get_engine()
        first_version = self.current_alembic_version()

        get_engine()
        second_version = self.current_alembic_version()

        self.assertEqual(first_version, second_version)

    def test_downgrade_to_base_removes_all_schema_tables(self):
        get_engine()
        self.assertTrue(self.table_names() >= EXPECTED_TABLES)

        command.downgrade(self._alembic_config(), "base")

        self.assertEqual(self.table_names(), {"alembic_version"})

    def test_upgrade_again_after_downgrade_rebuilds_schema(self):
        get_engine()
        command.downgrade(self._alembic_config(), "base")

        command.upgrade(self._alembic_config(), "head")

        self.assertEqual(
            self.table_names(),
            EXPECTED_TABLES,
        )
        self.assertEqual(self.current_alembic_version(), "0001_initial_schema")


if __name__ == "__main__":
    unittest.main()
