import simplejson
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from config import LidlConfig
from config import storage_config
from export.json_export import export_receipts_from_db
from shared.receipt_schema import normalize_receipt_schema
from shared.retailer_runtime import get_retailer_runtime
from storage import (
    SqliteReceiptStore,
    create_receipt_store,
)


class ReceiptStoreTests(unittest.TestCase):
    def isolated_receipts_db(self) -> Path:
        tmp_dir = self.enterContext(tempfile.TemporaryDirectory())
        db_path = Path(tmp_dir) / "receipts.sqlite"
        self.enterContext(patch.object(storage_config, "SQLITE_RECEIPTS_DB_FILE", str(db_path)))
        return db_path

    @staticmethod
    def execute(db_path: Path, sql: str, params: tuple[object, ...] = ()) -> None:
        with closing(sqlite3.connect(db_path)) as connection:
            connection.execute(sql, params)
            connection.commit()

    @staticmethod
    def query_one(db_path: Path, sql: str, params: tuple[object, ...] = ()):
        with closing(sqlite3.connect(db_path)) as connection:
            return connection.execute(sql, params).fetchone()

    @staticmethod
    def query_all(db_path: Path, sql: str, params: tuple[object, ...] = ()):
        with closing(sqlite3.connect(db_path)) as connection:
            return connection.execute(sql, params).fetchall()

    def test_create_receipt_store_returns_sqlite_store_by_default(self):
        store = create_receipt_store()

        self.assertIsInstance(store, SqliteReceiptStore)


    def test_sqlite_receipt_store_fetch_existing_ids_follows_public_api(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        store.persist_receipts(
            [
                {
                    "id": "rewe-0605-8-01042026-1908-7714",
                    "retailer": "rewe",
                    "purchase_date": "01.04.2026",
                    "store": "REWE Markt GmbH",
                    "address": {
                        "street": "Kaiserstr.",
                        "street_no": "22",
                        "zip": "90763",
                        "city": "Fürth",
                    },
                    "total_price": "1,00",
                    "payment_methods": [{"method": "Karte", "network": "VISA", "amount": "1,00"}],
                    "items": [{"name": "Banane", "price": "1,00", "quantity": "1", "unit": "stk"}],
                }
            ],
            retailer="rewe",
        )

        existing_ids = store.find_existing_ids(retailer="rewe")

        self.assertEqual(existing_ids, {"rewe-0605-8-01042026-1908-7714"})

    def test_sqlite_receipt_store_fetch_existing_ids_does_not_depend_on_hash(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        store.persist_receipts(
            [
                {
                    "id": "rewe-0605-8-01042026-1908-7714",
                    "retailer": "rewe",
                    "purchase_date": "01.04.2026",
                    "store": "REWE Markt GmbH",
                    "address": {
                        "street": "Kaiserstr.",
                        "street_no": "22",
                        "zip": "90763",
                        "city": "Fürth",
                    },
                    "total_price": "1,00",
                }
            ],
            retailer="rewe",
        )

        self.execute(
            db_path,
            "update purchase set hash = ? where id = ?",
            ("kaputt", "rewe-0605-8-01042026-1908-7714"),
        )

        existing_ids = store.find_existing_ids(retailer="rewe")

        self.assertEqual(existing_ids, {"rewe-0605-8-01042026-1908-7714"})

    def test_sqlite_receipt_store_applies_sql_migrations_once_and_creates_all_tables(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()

        self.assertEqual(store.find_existing_ids(retailer="rewe"), set())
        self.assertEqual(store.find_existing_ids(retailer="rewe"), set())

        table_names = {
            row[0]
            for row in self.query_all(db_path, "select name from sqlite_master where type = 'table'")
        }
        index_names = {
            row[0]
            for row in self.query_all(db_path, "select name from sqlite_master where type = 'index'")
        }
        purchase_columns = {
            row[1]
            for row in self.query_all(db_path, "pragma table_info(purchase)")
        }
        applied_migrations = self.query_all(
            db_path,
            "select version, script_name from schema_migration order by version",
        )

        self.assertTrue(
            {
                "schema_migration",
                "retailer",
                "store",
                "purchase",
                "purchase_item",
                "payment_method",
                "purchase_lidl",
                "purchase_rewe",
            }.issubset(table_names)
        )
        self.assertTrue(
            any(
                name in index_names
                for name in ("uq_purchase_item__purchase_position", "sqlite_autoindex_purchase_item_1")
            )
        )
        self.assertTrue(
            any(
                name in index_names
                for name in ("uq_payment_method__purchase_position", "sqlite_autoindex_payment_method_1")
            )
        )
        self.assertEqual(
            applied_migrations,
            [
                ("V001", "V001__core_schema.sql"),
            ],
        )

    def test_sqlite_receipt_store_persist_receipts_migrates_precreated_empty_db_file(self):
        db_path = self.isolated_receipts_db()
        sqlite3.connect(db_path).close()

        store = SqliteReceiptStore()
        result = store.persist_receipts(
            [
                {
                    "id": "rewe-4196-4-12022026-1103-2587",
                    "retailer": "rewe",
                    "purchase_date": "12.02.2026",
                    "store": "R E W E",
                    "total_price": 8.22,
                }
            ],
            retailer="rewe",
        )

        retailer_row = self.query_one(
            db_path,
            "select code from retailer where code = ?",
            ("rewe",),
        )

        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.total_receipts, 1)
        self.assertEqual(retailer_row, ("rewe",))

    def test_sqlite_receipt_store_persists_lidl_retailer_country_from_runtime_config(self):
        original_country = LidlConfig.COUNTRY
        try:
            LidlConfig.set_country("bg")
            expected_profile = get_retailer_runtime("lidl")

            db_path = self.isolated_receipts_db()
            store = SqliteReceiptStore()
            store.persist_receipts(
                [
                    {
                        "id": "23004426420240828113520",
                        "retailer": "lidl",
                        "purchase_date": "28.08.2024",
                        "store": "lidl",
                        "total_price": 19.23,
                    }
                ],
                retailer="lidl",
            )

            retailer_row = self.query_one(
                db_path,
                "select code, name, country from retailer where code = ?",
                ("lidl",),
            )

            self.assertEqual(
                retailer_row,
                (
                    expected_profile.code,
                    expected_profile.name,
                    expected_profile.country,
                ),
            )
        finally:
            LidlConfig.set_country(original_country)

    def test_export_receipts_from_db_writes_json(self):
        db_path = self.isolated_receipts_db()
        output_file = db_path.parent / "lidl_receipts.json"
        sqlite_store = SqliteReceiptStore()
        sqlite_store.persist_receipts(
            [
                {
                    "id": "23004426420240828113520",
                    "retailer": "lidl",
                    "purchase_date": "28.08.2024",
                    "store": "lidl",
                    "total_price": 19.23,
                }
            ],
            retailer="lidl",
        )

        exported_count = export_receipts_from_db(
            retailer="lidl",
            output_file=str(output_file),
        )

        exported_payload = simplejson.loads(output_file.read_text(encoding="utf-8"))

        self.assertEqual(exported_count, 1)
        self.assertEqual(exported_payload[0]["id"], "23004426420240828113520")
        self.assertEqual(exported_payload[0]["purchase_date"], "2024-08-28")

    # JSON-write upsert/sort tests wurden entfernt, da JSON jetzt nur noch Exportformat ist.

    def test_sqlite_receipt_store_persists_relational_rows_and_updates_existing_receipt(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        rewe_receipt = {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": "01.04.2026",
                "store": "REWE Markt GmbH",
                "address": {
                    "street": "Kaiserstr.",
                    "street_no": "22",
                    "zip": "90763",
                    "city": "Fürth",
                },
                "market": "5802",
                "register": "4",
                "cashier": "A123",
                "total_price": "1,00",
                "rewe_bonus_amount": 0.5,
                "rewe_bonus_total_amount": 10.17,
                "rewe_bonus_discount": 0.0,
                "payment_methods": [{"method": "Karte", "network": "VISA", "amount": "1,00"}],
                "items": [{"name": "Banane", "price": "1,00", "quantity": "1", "unit": "stk"}],
        }
        lidl_receipt = {
                "id": "23004426420240828113520",
                "retailer": "lidl",
                "purchase_date": "28.08.2024",
                "store": "lidl",
                "address": {
                    "street": "Hauptstr.",
                    "street_no": "5",
                    "zip": "90762",
                    "city": "Fürth",
                },
                "total_price": 19.23,
                "lidlplus_discount": 1.5,
                "sticker_discount": 0.8,
                "payment_methods": [{"method": "Karte", "network": "VISA", "amount": 19.23}],
                "items": [{"name": "Tomaten", "price": "3,99", "quantity": "0,696", "unit": "kg"}],
        }

        rewe_result = store.persist_receipts([rewe_receipt], retailer="rewe")
        lidl_result = store.persist_receipts([lidl_receipt], retailer="lidl")
        updated_rewe_result = store.persist_receipts(
            [
                {
                    **rewe_receipt,
                    "total_price": "1,99",
                    "items": [{"name": "Banane", "price": "1,99", "quantity": "1", "unit": "stk"}],
                }
            ],
            retailer="rewe",
        )

        self.assertEqual((rewe_result.created_count, rewe_result.updated_count, rewe_result.total_receipts), (1, 0, 1))
        self.assertEqual((lidl_result.created_count, lidl_result.updated_count, lidl_result.total_receipts), (1, 0, 1))
        self.assertEqual(
            (updated_rewe_result.created_count, updated_rewe_result.updated_count, updated_rewe_result.total_receipts),
            (0, 1, 1),
        )

        purchase_count = self.query_one(db_path, "select count(*) from purchase")[0]
        rewe_count = self.query_one(db_path, "select count(*) from purchase_rewe")[0]
        lidl_count = self.query_one(db_path, "select count(*) from purchase_lidl")[0]
        item_rows = self.query_all(
            db_path,
            "select purchase_id, position, name, quantity, unit, price from purchase_item order by purchase_id, position",
        )
        payment_rows = self.query_all(
            db_path,
            "select purchase_id, position, method, network, amount from payment_method order by purchase_id, position",
        )
        store_count = self.query_one(db_path, "select count(*) from store")[0]

        self.assertEqual(purchase_count, 2)
        self.assertEqual(rewe_count, 1)
        self.assertEqual(lidl_count, 1)
        self.assertEqual(store_count, 2)
        self.assertEqual(len(item_rows), 2)
        self.assertEqual(len(payment_rows), 2)
        self.assertEqual(item_rows[0][0], "23004426420240828113520")
        self.assertEqual(item_rows[1][0], "rewe-0605-8-01042026-1908-7714")
        self.assertEqual(item_rows[1][5], 1.99)
        self.assertEqual(payment_rows[1][3], "VISA")

    def test_sqlite_receipt_store_persists_purchase_date_in_iso_format(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        store.persist_receipts(
            [
                {
                    "id": "rewe-0605-8-01042026-1908-7714",
                    "retailer": "rewe",
                    "purchase_date": "01.04.2026",
                    "store": "REWE Markt GmbH",
                    "total_price": "1,00",
                }
            ],
            retailer="rewe",
        )

        persisted_purchase_date = self.query_one(
            db_path,
            "select purchase_date from purchase where id = ?",
            ("rewe-0605-8-01042026-1908-7714",),
        )

        self.assertEqual(persisted_purchase_date, ("2026-04-01",))

    def test_sqlite_receipt_store_upsert_skips_unchanged_receipts_by_hash(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        receipt = {
            "id": "rewe-0605-8-01042026-1908-7714",
            "retailer": "rewe",
            "purchase_date": "01.04.2026",
            "store": "REWE Markt GmbH",
            "address": {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": "90763",
                "city": "Fürth",
            },
            "total_price": "1,00",
            "payment_methods": [{"method": "Karte", "network": "VISA", "amount": "1,00"}],
            "items": [{"name": "Banane", "price": "1,00", "quantity": "1", "unit": "stk"}],
        }

        first_result = store.persist_receipts([receipt], retailer="rewe")
        second_result = store.persist_receipts([receipt], retailer="rewe")

        purchase_count = self.query_one(db_path, "select count(*) from purchase")[0]
        item_count = self.query_one(db_path, "select count(*) from purchase_item")[0]
        payment_count = self.query_one(db_path, "select count(*) from payment_method")[0]

        self.assertEqual((first_result.created_count, first_result.updated_count, first_result.total_receipts), (1, 0, 1))
        self.assertEqual((second_result.created_count, second_result.updated_count, second_result.total_receipts), (0, 0, 1))
        self.assertEqual(purchase_count, 1)
        self.assertEqual(item_count, 1)
        self.assertEqual(payment_count, 1)

    def test_sqlite_receipt_store_persist_receipts_reuses_provided_payload_hash(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        result = store.persist_receipts(
            [
                {
                    "id": "23004426420240828113520",
                    "retailer": "lidl",
                    "purchase_date": "28.08.2024",
                    "store": "lidl",
                    "total_price": 19.23,
                    "payload_hash": "payload-lidl-2",
                }
            ],
            retailer="lidl",
        )

        persisted_hash = self.query_one(
            db_path,
            "select hash from purchase where id = ?",
            ("23004426420240828113520",),
        )

        self.assertEqual((result.created_count, result.updated_count, result.total_receipts), (1, 0, 1))
        self.assertEqual(persisted_hash, ("payload-lidl-2",))

    def test_sqlite_receipt_store_replace_update_rebuilds_child_rows_without_stale_positions(self):
        db_path = self.isolated_receipts_db()
        store = SqliteReceiptStore()
        original_receipt = {
            "id": "rewe-0605-8-01042026-1908-7714",
            "retailer": "rewe",
            "purchase_date": "01.04.2026",
            "store": "REWE Markt GmbH",
            "address": {
                "street": "Kaiserstr.",
                "street_no": "22",
                "zip": "90763",
                "city": "Fürth",
            },
            "total_price": "3,00",
            "payment_methods": [
                {"method": "Karte", "network": "VISA", "amount": "3,00"},
                {"method": "Coupon", "amount": "0,50"},
            ],
            "items": [
                {"name": "Banane", "price": "1,00", "quantity": "1", "unit": "stk"},
                {"name": "Apfel", "price": "2,00", "quantity": "1", "unit": "stk"},
            ],
        }
        updated_receipt = {
            **original_receipt,
            "total_price": "1,50",
            "payment_methods": [{"method": "Karte", "network": "VISA", "amount": "1,50"}],
            "items": [{"name": "Banane", "price": "1,50", "quantity": "1", "unit": "stk"}],
        }

        first_result = store.persist_receipts([original_receipt], retailer="rewe")
        second_result = store.persist_receipts([updated_receipt], retailer="rewe")

        item_rows = self.query_all(
            db_path,
            "select position, name, price from purchase_item where purchase_id = ? order by position",
            ("rewe-0605-8-01042026-1908-7714",),
        )
        payment_rows = self.query_all(
            db_path,
            "select position, method, amount from payment_method where purchase_id = ? order by position",
            ("rewe-0605-8-01042026-1908-7714",),
        )

        self.assertEqual((first_result.created_count, first_result.updated_count), (1, 0))
        self.assertEqual((second_result.created_count, second_result.updated_count), (0, 1))
        self.assertEqual(item_rows, [(1, "Banane", 1.5)])
        self.assertEqual(payment_rows, [(1, "Karte", 1.5)])

    def test_shared_receipt_schema_keeps_lidl_fields_neutral_and_normalizes_quantities(self):
        payload = {
            "id": "23004426420240828113520",
            "purchase_date": "28.08.2024",
            "address": {"zip": "90762"},
            "items": [{"name": "Tomaten", "price": "3,99", "quantity": "0,696", "unit": "kg"}],
        }

        normalized_shared = normalize_receipt_schema(payload, retailer="lidl")

        self.assertEqual(normalized_shared["purchase_date"], "2024-08-28")
        self.assertEqual(normalized_shared["address"]["zip"], 90762)
        # Lidl-specific fields are present with defaults when retailer is lidl
        self.assertIn("lidlplus_discount", normalized_shared)
        self.assertIsNone(normalized_shared["lidlplus_discount"])
        # REWE fields are NOT present for lidl retailer
        self.assertNotIn("rewe_bonus_amount", normalized_shared)
        self.assertEqual(normalized_shared["items"][0]["quantity"], 0.696)


if __name__ == "__main__":
    unittest.main()
