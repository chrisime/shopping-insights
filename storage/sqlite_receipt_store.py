"""SQLite-backed receipt store with relational projections and payload hashes."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from config import get_receipt_schema_profile
from config import storage_config
from result_types import PersistResult
from shared.receipt_dto import (
    AddressDTO,
    PaymentMethodDTO,
    ReceiptDTO,
    ReceiptItemDTO,
    receipt_dict_to_dto,
    receipt_dto_to_dict,
)
from shared.receipt_hashes import calculate_receipt_payload_hash
from shared.receipt_schema import normalize_receipt_schema
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
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    """Apply all pending SQLite migrations before the store is used."""
    apply_sqlite_migrations(connection)
    connection.commit()


def _persist_receipt_row(receipt: ReceiptDTO, payload_hash: str, connection: sqlite3.Connection) -> Optional[str]:
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

    if retailer_code == "lidl":
        purchase_lidl_domain.insert(build_purchase_lidl_entity(receipt))
    elif retailer_code == "rewe":
        purchase_rewe_domain.insert(build_purchase_rewe_entity(receipt))

    purchase_item_domain.insert_many(build_purchase_item_entities(receipt))
    payment_method_domain.insert_many(build_payment_method_entities(receipt))
    return action


def _map_purchase_to_receipt_dict(
    purchase: Any,
    retailer: str,
    connection: sqlite3.Connection,
) -> Dict[str, Any]:
    """Map one persisted purchase aggregate back to the canonical receipt dictionary."""
    store_domain = StoreDomain(connection)
    purchase_item_domain = PurchaseItemDomain(connection)
    payment_method_domain = PaymentMethodDomain(connection)
    purchase_lidl_domain = PurchaseLidlDomain(connection)
    purchase_rewe_domain = PurchaseReweDomain(connection)

    if purchase.store_id is None:
        store_name = ""
        address = AddressDTO(street="", street_no="", zip="", city="")
    else:
        store = store_domain.find_by_id(purchase.store_id)
        if store is None:
            store_name = ""
            address = AddressDTO(street="", street_no="", zip="", city="")
        else:
            store_name = store.name
            address = AddressDTO(
                street=store.street,
                street_no=store.street_no,
                zip=store.zip,
                city=store.city,
            )

    items = purchase_item_domain.find_by_purchase_id(purchase.id)
    payment_methods = payment_method_domain.find_by_purchase_id(purchase.id)
    lidl_extension = purchase_lidl_domain.find_by_purchase_id(purchase.id)
    rewe_extension = purchase_rewe_domain.find_by_purchase_id(purchase.id)

    receipt_dto = ReceiptDTO(
        id=purchase.id,
        retailer=retailer,
        purchase_date=purchase.purchase_date,
        store=store_name,
        address=address,
        market=purchase.market,
        register_id=purchase.register_id,
        cashier=purchase.cashier,
        total_price=purchase.total_price,
        amount_saved=purchase.amount_saved,
        saved_deposit=purchase.saved_deposit,
        currency=purchase.currency,
        source_file=purchase.source_file,
        payload_hash=purchase.hash,
        items=tuple(
            ReceiptItemDTO(
                position=item.position,
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                price=item.price,
            )
            for item in items
        ),
        payment_methods=tuple(
            PaymentMethodDTO(
                position=payment_method.position,
                method=payment_method.method,
                network=payment_method.network,
                amount=payment_method.amount,
            )
            for payment_method in payment_methods
        ),
        lidlplus_amount_saved=None if lidl_extension is None else lidl_extension.lidlplus_amount_saved,
        sticker_discount_amount=None if lidl_extension is None else lidl_extension.sticker_discount_amount,
        rewe_bonus_amount=None if rewe_extension is None else rewe_extension.rewe_bonus_amount,
        rewe_bonus_total_amount=None if rewe_extension is None else rewe_extension.rewe_bonus_total_amount,
        rewe_bonus_amount_saved=None if rewe_extension is None else rewe_extension.rewe_bonus_amount_saved,
    )
    return receipt_dto_to_dict(receipt_dto)


class SqliteReceiptStore(ReceiptStore):
    """SQLite-backed receipt store used for relational persistence plus delta checks."""

    def find_existing_ids(self, retailer: str) -> set[str]:
        with closing(_connect_sqlite()) as connection:
            purchase_domain = PurchaseDomain(connection)
            return purchase_domain.find_ids_by_retailer(retailer)


    def list_receipts(self, retailer: str) -> list[Dict[str, Any]]:
        """Load all persisted receipts for one retailer and map them to schema dictionaries."""
        with closing(_connect_sqlite()) as connection:
            purchase_domain = PurchaseDomain(connection)

            receipts = [
                _map_purchase_to_receipt_dict(
                    purchase,
                    retailer=retailer,
                    connection=connection,
                )
                for purchase in purchase_domain.find_by_retailer(retailer)
            ]

        return receipts

    def persist_receipts(self, receipts: Sequence[Dict[str, Any]], retailer: str) -> PersistResult:
        created_count = 0
        updated_count = 0

        retailer_code = retailer.lower()
        receipt_schema_profile = get_receipt_schema_profile(retailer_code)
        retailer_entity = build_retailer_entity(retailer_code)

        with closing(_connect_sqlite()) as connection:
            retailer_domain = RetailerDomain(connection)
            purchase_domain = PurchaseDomain(connection)

            with connection:
                retailer_domain.upsert(retailer_entity)

                for receipt in receipts:
                    normalized_receipt = normalize_receipt_schema(receipt, retailer_code, receipt_schema_profile)
                    receipt_id = normalized_receipt.get("id") or normalized_receipt.get("url")

                    if not receipt_id:
                        continue

                    normalized_receipt["id"] = str(receipt_id)
                    payload_hash = str(
                        normalized_receipt.get("payload_hash")
                        or calculate_receipt_payload_hash(normalized_receipt)
                    )
                    normalized_receipt["payload_hash"] = payload_hash

                    receipt_dto = receipt_dict_to_dto(normalized_receipt, retailer_code)

                    action = _persist_receipt_row(receipt_dto, payload_hash, connection)

                    if action == "created":
                        created_count += 1
                    elif action == "updated":
                        updated_count += 1

                total_receipts = purchase_domain.count_by_retailer(retailer_code)

        return PersistResult(
            created_count=created_count,
            updated_count=updated_count,
            total_receipts=total_receipts,
        )
