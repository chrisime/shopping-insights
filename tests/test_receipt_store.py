import simplejson
import sqlite3
import tempfile
import unittest
from pathlib import Path

from config import LidlConfig, get_retailer_runtime
from shared.receipt_schema import normalize_receipt_schema
from storage import (
    WRITE_BACKENDS,
    SqliteReceiptStore,
    create_receipt_store,
    resolve_receipt_store_target,
)
from storage.json_receipt_store import JsonReceiptStore, sort_receipts_by_date, upsert_receipts


class ReceiptStoreTests(unittest.TestCase):
    def test_storage_module_exports_available_write_backends(self):
        self.assertEqual(WRITE_BACKENDS, ("json", "sqlite"))

    def test_create_receipt_store_returns_json_store_for_default_backend(self):
        store = create_receipt_store()

        self.assertIsInstance(store, JsonReceiptStore)

    def test_create_receipt_store_returns_sqlite_store_for_sqlite_backend(self):
        store = create_receipt_store("sqlite")

        self.assertIsInstance(store, SqliteReceiptStore)

    def test_create_receipt_store_rejects_unknown_backend(self):
        with self.assertRaisesRegex(ValueError, "Unbekanntes Write-Backend"):
            create_receipt_store("db")

    def test_json_receipt_store_fetch_existing_ids_follows_public_api(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "receipts.json"
            file_path.write_text(
                simplejson.dumps([
                    {"id": "a", "purchase_date": "2026.05.01"},
                    {"url": "legacy-b", "purchase_date": "2026.04.01"},
                ]),
                encoding="utf-8",
            )

            store = JsonReceiptStore()
            existing_ids = store.find_existing_ids(
                retailer="rewe",
                file_path=str(file_path),
            )

        self.assertEqual(existing_ids, {"a", "legacy-b"})

    def test_json_receipt_store_fetch_existing_ids_tolerates_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "receipts.json"
            file_path.write_text("{kaputt", encoding="utf-8")

            store = JsonReceiptStore()
            existing_ids = store.find_existing_ids(retailer="rewe", file_path=str(file_path))

        self.assertEqual(existing_ids, set())

    def test_sqlite_receipt_store_fetch_existing_ids_follows_public_api(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            store = SqliteReceiptStore()
            store.persist_receipts(
                [
                    {
                        "id": "rewe-0605-8-01042026-1908-7714",
                        "retailer": "rewe",
                        "purchase_date": "2026.04.01",
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
                file_path=str(db_path),
            )

            existing_ids = store.find_existing_ids(retailer="rewe", file_path=str(db_path))

        self.assertEqual(existing_ids, {"rewe-0605-8-01042026-1908-7714"})

    def test_sqlite_receipt_store_fetch_existing_ids_does_not_depend_on_hash(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            store = SqliteReceiptStore()
            store.persist_receipts(
                [
                    {
                        "id": "rewe-0605-8-01042026-1908-7714",
                        "retailer": "rewe",
                        "purchase_date": "2026.04.01",
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
                file_path=str(db_path),
            )

            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    "update purchase set hash = ? where id = ?",
                    ("kaputt", "rewe-0605-8-01042026-1908-7714"),
                )
                connection.commit()

            existing_ids = store.find_existing_ids(retailer="rewe", file_path=str(db_path))

        self.assertEqual(existing_ids, {"rewe-0605-8-01042026-1908-7714"})

    def test_sqlite_receipt_store_applies_sql_migrations_once_and_creates_all_tables(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            store = SqliteReceiptStore()

            self.assertEqual(store.find_existing_ids(retailer="rewe", file_path=str(db_path)), set())
            self.assertEqual(store.find_existing_ids(retailer="rewe", file_path=str(db_path)), set())

            with sqlite3.connect(db_path) as connection:
                table_names = {
                    row[0]
                    for row in connection.execute(
                        "select name from sqlite_master where type = 'table'"
                    ).fetchall()
                }
                index_names = {
                    row[0]
                    for row in connection.execute(
                        "select name from sqlite_master where type = 'index'"
                    ).fetchall()
                }
                applied_migrations = connection.execute(
                    "select version, script_name from schema_migration order by version"
                ).fetchall()

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
            {
                "uq_purchase_item__purchase_position",
                "uq_payment_method__purchase_position",
            }.issubset(index_names)
        )
        self.assertEqual(
            applied_migrations,
            [
                ("V001", "V001__core_schema.sql"),
                ("V002", "V002__purchase_lidl.sql"),
                ("V003", "V003__purchase_rewe.sql"),
            ],
        )

    def test_sqlite_receipt_store_persist_receipts_migrates_precreated_empty_db_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            sqlite3.connect(db_path).close()

            store = SqliteReceiptStore()
            result = store.persist_receipts(
                [
                    {
                        "id": "rewe-4196-4-12022026-1103-2587",
                        "retailer": "rewe",
                        "purchase_date": "2026.02.12",
                        "store": "R E W E",
                        "total_price": 8.22,
                    }
                ],
                retailer="rewe",
                file_path=str(db_path),
            )

            with sqlite3.connect(db_path) as connection:
                retailer_row = connection.execute(
                    "select code from retailer where code = ?",
                    ("rewe",),
                ).fetchone()

        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.total_receipts, 1)
        self.assertEqual(retailer_row, ("rewe",))

    def test_sqlite_receipt_store_persists_lidl_retailer_country_from_runtime_config(self):
        original_country = LidlConfig.COUNTRY
        try:
            LidlConfig.set_country("bg")
            expected_profile = get_retailer_runtime("lidl")

            with tempfile.TemporaryDirectory() as tmp_dir:
                db_path = Path(tmp_dir) / "receipts.sqlite"
                store = SqliteReceiptStore()
                store.persist_receipts(
                    [
                        {
                            "id": "23004426420240828113520",
                            "retailer": "lidl",
                            "purchase_date": "2024.08.28",
                            "store": "lidl",
                            "total_price": 19.23,
                        }
                    ],
                    retailer="lidl",
                    file_path=str(db_path),
                )

                with sqlite3.connect(db_path) as connection:
                    retailer_row = connection.execute(
                        "select code, name, country from retailer where code = ?",
                        ("lidl",),
                    ).fetchone()

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


    def test_resolve_receipt_store_target_returns_backend_specific_default_paths(self):
        self.assertEqual(resolve_receipt_store_target("json", retailer="lidl"), "lidl_receipts.json")
        self.assertEqual(resolve_receipt_store_target("json", retailer="rewe"), "rewe_receipts.json")
        self.assertEqual(resolve_receipt_store_target("sqlite", retailer="rewe"), "shopping_receipts.sqlite")

    def test_resolve_receipt_store_target_rejects_unknown_json_retailer(self):
        with self.assertRaisesRegex(ValueError, "Unbekannter Händler für Receipt-Storage"):
            resolve_receipt_store_target("json", retailer="aldi")

    def test_upsert_receipts_normalizes_and_updates_legacy_url_records(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "receipts.json"
            file_path.write_text(
                simplejson.dumps(
                    [
                        {
                            "url": "rewe-0605-8-01042026-1908-7714",
                            "purchase_date": "01.04.2026 19:08",
                            "store": "REWE Markt GmbH",
                            "address": {
                                "street": " Kaiserstr. ",
                                "street_no": "22",
                                "zip": "90763",
                                "city": " Fürth ",
                            },
                            "total_price": "1,00",
                            "payment_methods": None,
                            "items": None,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            created_count, updated_count, total_count = upsert_receipts(
                [
                    {
                        "id": "rewe-0605-8-01042026-1908-7714",
                        "retailer": "rewe",
                        "purchase_date": "2026.04.01",
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
                file_path=str(file_path),
                retailer="rewe",
            )

            self.assertEqual((created_count, updated_count, total_count), (0, 1, 1))

            saved_receipts = simplejson.loads(file_path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved_receipts), 1)
            self.assertEqual(saved_receipts[0]["retailer"], "rewe")
            self.assertEqual(saved_receipts[0]["purchase_date"], "2026.04.01")
            self.assertEqual(saved_receipts[0]["address"]["zip"], 90763)
            self.assertEqual(saved_receipts[0]["payment_methods"][0]["amount"], 1.0)
            self.assertEqual(saved_receipts[0]["items"][0]["quantity"], 1)
            self.assertIsNone(saved_receipts[0]["rewe_bonus_amount"])
            self.assertIsNone(saved_receipts[0]["rewe_bonus_amount_saved"])

    def test_sort_receipts_by_date_orders_mixed_legacy_and_normalized_formats_descending(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "receipts.json"
            file_path.write_text(
                simplejson.dumps(
                    [
                        {
                            "id": "a",
                            "retailer": "lidl",
                            "purchase_date": "01.04.2026 10:15",
                        },
                        {
                            "id": "b",
                            "retailer": "rewe",
                            "purchase_date": "2026.05.02",
                        },
                        {
                            "id": "c",
                            "retailer": "lidl",
                            "purchase_date": "30.03.2026",
                        },
                    ]
                ),
                encoding="utf-8",
            )

            count = sort_receipts_by_date(file_path=str(file_path), retailer="lidl")

            self.assertEqual(count, 3)
            saved_receipts = simplejson.loads(file_path.read_text(encoding="utf-8"))
            self.assertEqual([receipt["id"] for receipt in saved_receipts], ["b", "a", "c"])

    def test_sqlite_receipt_store_persists_relational_rows_and_updates_existing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            store = SqliteReceiptStore()
            rewe_receipt = {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": "2026.04.01",
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
                "rewe_bonus_amount_saved": 0.0,
                "payment_methods": [{"method": "Karte", "network": "VISA", "amount": "1,00"}],
                "items": [{"name": "Banane", "price": "1,00", "quantity": "1", "unit": "stk"}],
            }
            lidl_receipt = {
                "id": "23004426420240828113520",
                "retailer": "lidl",
                "purchase_date": "2024.08.28",
                "store": "lidl",
                "address": {
                    "street": "Hauptstr.",
                    "street_no": "5",
                    "zip": "90762",
                    "city": "Fürth",
                },
                "total_price": 19.23,
                "lidlplus_amount_saved": 1.5,
                "sticker_discount_amount": 0.8,
                "payment_methods": [{"method": "Karte", "network": "VISA", "amount": 19.23}],
                "items": [{"name": "Tomaten", "price": "3,99", "quantity": "0,696", "unit": "kg"}],
            }

            rewe_result = store.persist_receipts([rewe_receipt], retailer="rewe", file_path=str(db_path))
            lidl_result = store.persist_receipts([lidl_receipt], retailer="lidl", file_path=str(db_path))
            updated_rewe_result = store.persist_receipts(
                [
                    {
                        **rewe_receipt,
                        "total_price": "1,99",
                        "items": [{"name": "Banane", "price": "1,99", "quantity": "1", "unit": "stk"}],
                    }
                ],
                retailer="rewe",
                file_path=str(db_path),
            )

            self.assertEqual((rewe_result.created_count, rewe_result.updated_count, rewe_result.total_receipts), (1, 0, 1))
            self.assertEqual((lidl_result.created_count, lidl_result.updated_count, lidl_result.total_receipts), (1, 0, 1))
            self.assertEqual(
                (updated_rewe_result.created_count, updated_rewe_result.updated_count, updated_rewe_result.total_receipts),
                (0, 1, 1),
            )

            with sqlite3.connect(db_path) as connection:
                purchase_count = connection.execute("select count(*) from purchase").fetchone()[0]
                rewe_count = connection.execute("select count(*) from purchase_rewe").fetchone()[0]
                lidl_count = connection.execute("select count(*) from purchase_lidl").fetchone()[0]
                item_rows = connection.execute(
                    "select purchase_id, position, name, quantity, unit, price from purchase_item order by purchase_id, position"
                ).fetchall()
                payment_rows = connection.execute(
                    "select purchase_id, position, method, network, amount from payment_method order by purchase_id, position"
                ).fetchall()
                store_count = connection.execute("select count(*) from store").fetchone()[0]

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

    def test_sqlite_receipt_store_upsert_skips_unchanged_receipts_by_hash(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            store = SqliteReceiptStore()
            receipt = {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": "2026.04.01",
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

            first_result = store.persist_receipts([receipt], retailer="rewe", file_path=str(db_path))
            second_result = store.persist_receipts([receipt], retailer="rewe", file_path=str(db_path))

            with sqlite3.connect(db_path) as connection:
                purchase_count = connection.execute("select count(*) from purchase").fetchone()[0]
                item_count = connection.execute("select count(*) from purchase_item").fetchone()[0]
                payment_count = connection.execute("select count(*) from payment_method").fetchone()[0]

        self.assertEqual((first_result.created_count, first_result.updated_count, first_result.total_receipts), (1, 0, 1))
        self.assertEqual((second_result.created_count, second_result.updated_count, second_result.total_receipts), (0, 0, 1))
        self.assertEqual(purchase_count, 1)
        self.assertEqual(item_count, 1)
        self.assertEqual(payment_count, 1)

    def test_sqlite_receipt_store_replace_update_rebuilds_child_rows_without_stale_positions(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "receipts.sqlite"
            store = SqliteReceiptStore()
            original_receipt = {
                "id": "rewe-0605-8-01042026-1908-7714",
                "retailer": "rewe",
                "purchase_date": "2026.04.01",
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

            first_result = store.persist_receipts([original_receipt], retailer="rewe", file_path=str(db_path))
            second_result = store.persist_receipts([updated_receipt], retailer="rewe", file_path=str(db_path))

            with sqlite3.connect(db_path) as connection:
                item_rows = connection.execute(
                    "select position, name, price from purchase_item where purchase_id = ? order by position",
                    ("rewe-0605-8-01042026-1908-7714",),
                ).fetchall()
                payment_rows = connection.execute(
                    "select position, method, amount from payment_method where purchase_id = ? order by position",
                    ("rewe-0605-8-01042026-1908-7714",),
                ).fetchall()

        self.assertEqual((first_result.created_count, first_result.updated_count), (1, 0))
        self.assertEqual((second_result.created_count, second_result.updated_count), (0, 1))
        self.assertEqual(item_rows, [(1, "Banane", 1.5)])
        self.assertEqual(payment_rows, [(1, "Karte", 1.5)])

    def test_shared_receipt_schema_keeps_lidl_fields_neutral_and_normalizes_quantities(self):
        payload = {
            "id": "23004426420240828113520",
            "purchase_date": "2024.08.28",
            "address": {"zip": "90762"},
            "items": [{"name": "Tomaten", "price": "3,99", "quantity": "0,696", "unit": "kg"}],
        }

        normalized_shared = normalize_receipt_schema(payload, retailer="lidl")

        self.assertEqual(normalized_shared["address"]["zip"], 90762)
        self.assertNotIn("lidlplus_amount_saved", normalized_shared)
        self.assertNotIn("rewe_bonus_amount", normalized_shared)
        self.assertEqual(normalized_shared["items"][0]["quantity"], 0.696)


if __name__ == "__main__":
    unittest.main()


