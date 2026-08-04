import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from storage.database import reset_engine_cache


class KpiStoreTests(TestCase):
    def setUp(self):
        reset_engine_cache()
        self.tmp_dir = self.enterContext(tempfile.TemporaryDirectory())
        db_path = Path(self.tmp_dir) / "receipts.sqlite"
        self.enterContext(patch("config.storage_config.SQLITE_RECEIPTS_DB_FILE", str(db_path)))
        self.seed()

    def seed(self):
        from storage.sqlite_receipt_store import SqliteReceiptStore
        from shared.receipt_schema import normalize_receipt_schema
        from shared.receipt_dto import receipt_dict_to_dto

        def dto(receipt, retailer):
            return receipt_dict_to_dto(normalize_receipt_schema(receipt, retailer), retailer)

        store = SqliteReceiptStore()
        store.persist_receipts(
            [
                dto(
                    {
                        "id": "r-1",
                        "retailer": "rewe",
                        "purchase_date": "2024-01-15",
                        "store": "REWE Markt GmbH",
                        "total_price": 38.20,
                    },
                    "rewe",
                )
            ],
            retailer="rewe",
        )
        store.persist_receipts(
            [
                dto(
                    {
                        "id": "l-1",
                        "retailer": "lidl",
                        "purchase_date": "2024-01-15",
                        "store": "lidl",
                        "total_price": 42.50,
                    },
                    "lidl",
                ),
                dto(
                    {
                        "id": "l-2",
                        "retailer": "lidl",
                        "purchase_date": "2024-02-10",
                        "store": "lidl",
                        "total_price": 15.00,
                    },
                    "lidl",
                ),
            ],
            retailer="lidl",
        )

    def test_spending_retailers_included(self):
        from storage.kpi_store import MetricsStore
        store = MetricsStore()
        rows = store.spending_by_day()
        assert len(rows) > 0
        for row in rows:
            assert isinstance(row.retailers, list)
            if row.receipt_count > 0:
                assert len(row.retailers) > 0

    def test_spending_by_retailer_filter(self):
        from storage.kpi_store import MetricsStore
        store = MetricsStore()
        rows = store.spending_by_day(retailer="lidl")
        assert rows
        for row in rows:
            assert set(row.retailers) == {"lidl"}
