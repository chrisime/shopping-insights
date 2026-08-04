"""SQLite-backed receipt store with relational projections and payload hashes."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy import Connection, select

from config import storage_config
from result_types import PersistResult
from shared.receipt_dto import ReceiptDTO, receipt_dto_to_dict
from shared.receipt_hashes import calculate_receipt_payload_hash
from shared.receipt_store import ReceiptStore

from .database import connect, get_engine
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
from .sqlite_schema import (
    payment_method_table,
    purchase_item_table,
    purchase_lidl_table,
    purchase_rewe_table,
    purchase_table,
    store_table,
)


def _persist_receipt_row(receipt: ReceiptDTO, payload_hash: str, connection: Connection) -> str | None:
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


def _delete_purchase_children(connection: Connection, purchase_id: str) -> None:
    """Delete all child rows of a purchase before re-inserting updated data.

    This replaces the old INSERT OR REPLACE pattern which triggered
    ON DELETE CASCADE unexpectedly (SQLite REPLACE = DELETE + INSERT).
    """
    for table in (
        purchase_item_table,
        payment_method_table,
        purchase_lidl_table,
        purchase_rewe_table,
    ):
        connection.execute(table.delete().where(table.c.purchase_id == purchase_id))


def _map_store_projection(purchase: PurchaseEntity, connection: Connection) -> tuple[str, str | None, dict[str, str]]:
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


def _map_purchase_to_receipt_dict(purchase: PurchaseEntity, retailer: str, connection: Connection) -> dict[str, Any]:
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
        with connect() as connection:
            purchase_domain = PurchaseDomain(connection)
            return purchase_domain.find_ids_by_retailer(retailer)

    @staticmethod
    def list_receipts(retailer: str) -> list[dict[str, Any]]:
        """Load all persisted receipts for one retailer and map them to schema dictionaries."""
        with connect() as connection:
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
        with connect() as connection:
            purchase_item_domain = PurchaseItemDomain(connection)
            purchase_ids = purchase_item_domain.find_purchase_ids_by_item_name(name)

            if not purchase_ids:
                return []

            stmt = (
                select(purchase_table.c.id)
                .join(store_table, store_table.c.id == purchase_table.c.store_id)
                .where(purchase_table.c.id.in_(purchase_ids))
            )
            if retailer:
                stmt = stmt.where(store_table.c.retailer_code == retailer.lower())
            if start_date:
                stmt = stmt.where(purchase_table.c.purchase_date >= start_date)
            if end_date:
                stmt = stmt.where(purchase_table.c.purchase_date <= end_date)
            stmt = stmt.order_by(purchase_table.c.purchase_date.desc(), purchase_table.c.id)

            rows = connection.execute(stmt).fetchall()

            purchase_domain = PurchaseDomain(connection)
            store_domain = StoreDomain(connection)
            matched_name_upper = name.upper()
            receipts: list[dict[str, Any]] = []
            for row in rows:
                purchase = purchase_domain.find_by_id(str(row._mapping["id"]))
                if purchase is None:
                    continue
                store_id = purchase.store_id
                actual_retailer = retailer or ""
                if store_id is not None:
                    store = store_domain.find_by_id(store_id)
                    if store is not None:
                        actual_retailer = store.retailer_code
                receipt = _map_purchase_to_receipt_dict(purchase, actual_retailer, connection)
                for item in receipt["items"]:
                    if str(item.get("name", "")).upper() == matched_name_upper:
                        item["matched"] = True
                receipts.append(receipt)

            return receipts

    @staticmethod
    def list_receipts_by_date_range(
        start_date: str,
        end_date: str,
        retailer: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        with connect() as connection:
            stmt = (
                select(purchase_table.c.id)
                .join(store_table, store_table.c.id == purchase_table.c.store_id)
                .where(purchase_table.c.purchase_date >= start_date)
                .where(purchase_table.c.purchase_date <= end_date)
            )
            if retailer:
                stmt = stmt.where(store_table.c.retailer_code == retailer.lower())
            stmt = stmt.order_by(purchase_table.c.purchase_date.desc(), purchase_table.c.id)

            rows = connection.execute(stmt).fetchall()

            purchase_domain = PurchaseDomain(connection)
            store_domain = StoreDomain(connection)
            receipts: list[dict[str, Any]] = []
            for row in rows:
                purchase = purchase_domain.find_by_id(str(row._mapping["id"]))
                if purchase is None:
                    continue
                actual_retailer = retailer or ""
                if purchase.store_id is not None:
                    store = store_domain.find_by_id(purchase.store_id)
                    if store is not None:
                        actual_retailer = store.retailer_code
                receipt = _map_purchase_to_receipt_dict(purchase, actual_retailer, connection)
                receipts.append(receipt)

            return receipts

    def persist_receipts(self, receipts: Sequence[ReceiptDTO], retailer: str) -> PersistResult:
        created_count = 0
        updated_count = 0

        retailer_code = retailer.lower()
        retailer_entity = build_retailer_entity(retailer_code)

        with get_engine().begin() as connection:
            retailer_domain = RetailerDomain(connection)
            purchase_domain = PurchaseDomain(connection)

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
