import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


class KpiStoreTests(TestCase):
    def setUp(self):
        self.tmp_dir = self.enterContext(tempfile.TemporaryDirectory())
        db_path = Path(self.tmp_dir) / "receipts.sqlite"
        self.enterContext(patch("config.storage_config.SQLITE_RECEIPTS_DB_FILE", str(db_path)))
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS store (id INTEGER PRIMARY KEY, retailer_code TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS purchase (id INTEGER PRIMARY KEY, store_id INTEGER NOT NULL REFERENCES store(id), purchase_date TEXT NOT NULL, total_price REAL);
            INSERT INTO store (id, retailer_code) VALUES (1, 'lidl'), (2, 'rewe');
            INSERT INTO purchase (id, store_id, purchase_date, total_price) VALUES (1, 1, '2024-01-15', 42.50), (2, 2, '2024-01-15', 38.20), (3, 1, '2024-02-10', 15.00);
        """)
        conn.close()

    def test_spending_retailers_included(self):
        from storage.kpi_store import MetricsStore
        store = MetricsStore()
        rows = store.spending_by_day()
        assert len(rows) > 0
        for row in rows:
            assert isinstance(row.retailers, list)
            if row.receipt_count > 0:
                assert len(row.retailers) > 0
