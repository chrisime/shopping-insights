"""SQLite-backed receipt store with relational projections and payload hashes."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional, Sequence

from config import storage_config
from result_types import PersistResult
from shared.receipt_dto import ReceiptDTO, receipt_dto_to_dict
from shared.receipt_hashes import calculate_receipt_payload_hash
from shared.receipt_store import ReceiptStore

from .sqlite_domains import (
    PaymentMethodDomain,
    PurchaseDomain,
    PurchaseItemDomain,
    PurchaseLidlDomain,
    PurchaseReweDomain,
    RetailerDomain,
    StoreDomain,
)
from .sqlite_entities import PurchaseEntity
from .sqlite_entity_builders import (
    build_payment_method_entities,
    build_purchase_entity,
    build_purchase_item_entities,
    build_purchase_lidl_entity,
    build_purchase_rewe_entity,
    build_retailer_entity,
    build_store_entity,
)
from .sqlite_migration_runner import apply_sqlite_migrations


def _connect_sqlite() -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled and schema ensured."""
    db_path = Path(storage_config.SQLITE_RECEIPTS_DB_FILE)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma foreign_keys = on")
    _ensure_schema(connection)
    connection.execute("pragma foreign_keys = on")
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    """Apply all pending SQLite migrations before the store is used."""
    apply_sqlite_migrations(connection)
    connection.commit()


def _persist_receipt_row(receipt: ReceiptDTO, payload_hash: str, connection: sqlite3.Connection) -> str | None:
    """Persist one receipt and return whether it was created, updated or unchanged."""
    store_domain = StoreDomain(connection)
    purchase_domain = PurchaseDomain(connection)
    purchase_item_domain = PurchaseItemDomain(connection)
    payment_method_domain = PaymentMethodDomain(connection)
    purchase_lidl_domain = PurchaseLidlDomain(connection)
    purchase_rewe_domain = PurchaseReweDomain(connection)

    retailer_code = receipt.retailer
    store_entity = build_store_entity(receipt)

    store_id = store_domain.resolve_id(store_entity)
    purchase_entity = build_purchase_entity(receipt, store_id, payload_hash)
    action = purchase_domain.persist(purchase_entity)
    if action is None:
        return None

    if action == "updated":
        _delete_purchase_children(connection, receipt.id)

    if retailer_code == "lidl":
        purchase_lidl_domain.insert(build_purchase_lidl_entity(receipt))
    elif retailer_code == "rewe":
        purchase_rewe_domain.insert(build_purchase_rewe_entity(receipt))

    purchase_item_domain.insert_many(build_purchase_item_entities(receipt))
    payment_method_domain.insert_many(build_payment_method_entities(receipt))
    return action


def _delete_purchase_children(connection: sqlite3.Connection, purchase_id: str) -> None:
    """Delete all child rows of a purchase before re-inserting updated data.

    This replaces the old INSERT OR REPLACE pattern which triggered
    ON DELETE CASCADE unexpectedly (SQLite REPLACE = DELETE + INSERT).
    """
    connection.execute("DELETE FROM purchase_item WHERE purchase_id = ?", (purchase_id,))
    connection.execute("DELETE FROM payment_method WHERE purchase_id = ?", (purchase_id,))
    connection.execute("DELETE FROM purchase_lidl WHERE purchase_id = ?", (purchase_id,))
    connection.execute("DELETE FROM purchase_rewe WHERE purchase_id = ?", (purchase_id,))


def _map_store_projection(purchase: PurchaseEntity, connection: sqlite3.Connection) -> tuple[str, str | None, dict[str, str]]:
    store_domain = StoreDomain(connection)
    store_id = purchase.store_id
    if store_id is None:
        raise RuntimeError(f"DB integrity error: purchase {purchase.id} has NULL store_id")

    store = store_domain.find_by_id(store_id)
    if store is None:
        raise RuntimeError(f"DB integrity error: store {store_id} for purchase {purchase.id} not found")

    return store.name, store.market, {
        "street": store.street,
        "street_no": store.street_no,
        "zip": store.zip,
        "city": store.city,
    }


def _map_item_rows(items: Sequence[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "price": item.price,
        }
        for item in items
    ]


def _map_payment_method_rows(payment_methods: Sequence[Any]) -> list[dict[str, Any]]:
    return [
        {
            "method": payment_method.method,
            "network": payment_method.network,
            "amount": payment_method.amount,
        }
        for payment_method in payment_methods
    ]


def _map_purchase_to_receipt_dict(purchase: PurchaseEntity, retailer: str, connection: sqlite3.Connection) -> dict[str, Any]:
    """Map one persisted purchase aggregate back to the canonical receipt dictionary."""
    purchase_item_domain = PurchaseItemDomain(connection)
    payment_method_domain = PaymentMethodDomain(connection)
    purchase_lidl_domain = PurchaseLidlDomain(connection)
    purchase_rewe_domain = PurchaseReweDomain(connection)

    store_name, market, address = _map_store_projection(purchase, connection)

    items = purchase_item_domain.find_by_purchase_id(purchase.id)
    payment_methods = payment_method_domain.find_by_purchase_id(purchase.id)
    lidl_extension = purchase_lidl_domain.find_by_purchase_id(purchase.id)
    rewe_extension = purchase_rewe_domain.find_by_purchase_id(purchase.id)

    return {
        "id": purchase.id,
        "retailer": retailer,
        "purchase_date": purchase.purchase_date,
        "store": store_name,
        "address": address,
        "market": market,
        "register": purchase.register_id,
        "register_id": purchase.register_id,
        "cashier": purchase.cashier,
        "bon_number": purchase.bon_number,
        "total_price": purchase.total_price,
        "discount": purchase.discount,
        "saved_deposit": purchase.saved_deposit,
        "currency": purchase.currency,
        "source_file": purchase.source_file,
        "payload_hash": purchase.hash,
        "items": _map_item_rows(items),
        "payment_methods": _map_payment_method_rows(payment_methods),
        "lidlplus_discount": None if lidl_extension is None else lidl_extension.lidlplus_discount,
        "sticker_discount": None if lidl_extension is None else lidl_extension.sticker_discount,
        "rewe_bonus_amount": None if rewe_extension is None else rewe_extension.rewe_bonus_amount,
        "rewe_bonus_total_amount": None if rewe_extension is None else rewe_extension.rewe_bonus_total_amount,
        "rewe_bonus_discount": None if rewe_extension is None else rewe_extension.rewe_bonus_discount,
    }


class SqliteReceiptStore(ReceiptStore):
    """SQLite-backed receipt store used for relational persistence plus delta checks."""

    def find_existing_ids(self, retailer: str) -> set[str]:
        with closing(_connect_sqlite()) as connection:
            purchase_domain = PurchaseDomain(connection)
            return purchase_domain.find_ids_by_retailer(retailer)


    @staticmethod
    def list_receipts(retailer: str) -> list[dict[str, Any]]:
        """Load all persisted receipts for one retailer and map them to schema dictionaries."""
        with closing(_connect_sqlite()) as connection:
            purchase_domain = PurchaseDomain(connection)
            purchases = purchase_domain.find_by_retailer(retailer)

            if not purchases:
                return []

            return [
                _map_purchase_to_receipt_dict(purchase, retailer, connection)
                for purchase in purchases
            ]


    @staticmethod
    def list_receipts_by_item(
        name: str,
        retailer: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        with closing(_connect_sqlite()) as connection:
            purchase_item_domain = PurchaseItemDomain(connection)
            purchase_ids = purchase_item_domain.find_purchase_ids_by_item_name(name)

            if not purchase_ids:
                return []

            placeholders = ",".join("?" for _ in purchase_ids)
            params: list[Any] = purchase_ids[:]
            where_clauses = [f"purchase.id IN ({placeholders})"]

            if retailer:
                where_clauses.append("store.retailer_code = ?")
                params.append(retailer.lower())

            if start_date:
                where_clauses.append("purchase.purchase_date >= ?")
                params.append(start_date)

            if end_date:
                where_clauses.append("purchase.purchase_date <= ?")
                params.append(end_date)

            rows = connection.execute(
                f"""
                SELECT purchase.id FROM purchase
                JOIN store ON store.id = purchase.store_id
                WHERE {' AND '.join(where_clauses)}
                ORDER BY purchase.purchase_date DESC, purchase.id
                """,
                params,
            ).fetchall()

            purchase_domain = PurchaseDomain(connection)
            matched_name_upper = name.upper()
            receipts: list[dict[str, Any]] = []
            for row in rows:
                purchase = purchase_domain.find_by_id(str(row["id"]))
                if purchase is None:
                    continue
                receipt = _map_purchase_to_receipt_dict(purchase, retailer or "", connection)
                for item in receipt["items"]:
                    if str(item.get("name", "")).upper() == matched_name_upper:
                        item["matched"] = True
                receipts.append(receipt)

            return receipts

    def persist_receipts(self, receipts: Sequence[ReceiptDTO], retailer: str) -> PersistResult:
        created_count = 0
        updated_count = 0

        retailer_code = retailer.lower()
        retailer_entity = build_retailer_entity(retailer_code)

        with closing(_connect_sqlite()) as connection:
            retailer_domain = RetailerDomain(connection)
            purchase_domain = PurchaseDomain(connection)

            with connection:
                retailer_domain.upsert(retailer_entity)

                for receipt in receipts:
                    payload_hash = calculate_receipt_payload_hash(receipt_dto_to_dict(receipt))
                    action = _persist_receipt_row(receipt, payload_hash, connection)

                    if action == "created":
                        created_count += 1
                    elif action == "updated":
                        updated_count += 1

                total_receipts = purchase_domain.count_by_retailer(retailer_code)

        return PersistResult(created_count, updated_count, total_receipts)
