"""SQLAlchemy Core based SQLite domains for receipt persistence.

Every domain operates on a checked-out SQLAlchemy ``Connection``. Transactions
are managed by the caller (see ``storage.sqlite_receipt_store``), matching the
previous behaviour where each store call opened a connection.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import Connection, Row, Select, func, select
from sqlalchemy.sql import insert as insert_stmt

from .sqlite_entities import (
    PaymentMethodEntity,
    PurchaseEntity,
    PurchaseItemEntity,
    PurchaseLidlEntity,
    PurchaseReweEntity,
    RetailerEntity,
    StoreEntity,
)
from .sqlite_schema import (
    payment_method_table,
    purchase_item_table,
    purchase_lidl_table,
    purchase_rewe_table,
    purchase_table,
    retailer_table,
    store_table,
)


def _map_retailer_row(row: Row) -> RetailerEntity:
    return RetailerEntity(
        code=str(row._mapping["code"]),
        name=str(row._mapping["name"]),
        country=str(row._mapping["country"]),
    )


def _map_store_row(row: Row) -> StoreEntity:
    return StoreEntity(
        id=int(row._mapping["id"]),
        retailer_code=str(row._mapping["retailer_code"]),
        name=str(row._mapping["name"]),
        market=None if row._mapping["market"] is None else str(row._mapping["market"]),
        street=str(row._mapping["street"]),
        street_no=str(row._mapping["street_no"]),
        zip=str(row._mapping["zip"]),
        city=str(row._mapping["city"]),
        hash=str(row._mapping["hash"]),
    )


def _map_purchase_row(row: Row) -> PurchaseEntity:
    return PurchaseEntity(
        id=str(row._mapping["id"]),
        store_id=None if row._mapping["store_id"] is None else int(row._mapping["store_id"]),
        purchase_date=str(row._mapping["purchase_date"]),
        bon_number=None if row._mapping["bon_number"] is None else str(row._mapping["bon_number"]),
        register_id=None if row._mapping["register_id"] is None else str(row._mapping["register_id"]),
        cashier=None if row._mapping["cashier"] is None else str(row._mapping["cashier"]),
        total_price=None if row._mapping["total_price"] is None else float(row._mapping["total_price"]),
        discount=float(row._mapping["discount"]),
        saved_deposit=float(row._mapping["saved_deposit"]),
        currency=str(row._mapping["currency"]),
        source_file=None if row._mapping["source_file"] is None else str(row._mapping["source_file"]),
        hash=str(row._mapping["hash"]),
    )


def _map_purchase_item_row(row: Row) -> PurchaseItemEntity:
    return PurchaseItemEntity(
        id=int(row._mapping["id"]),
        purchase_id=str(row._mapping["purchase_id"]),
        position=int(row._mapping["position"]),
        name=str(row._mapping["name"]),
        quantity=float(row._mapping["quantity"]),
        unit=str(row._mapping["unit"]),
        price=float(row._mapping["price"]),
    )


def _map_payment_method_row(row: Row) -> PaymentMethodEntity:
    return PaymentMethodEntity(
        id=int(row._mapping["id"]),
        purchase_id=str(row._mapping["purchase_id"]),
        position=int(row._mapping["position"]),
        method=str(row._mapping["method"]),
        network=None if row._mapping["network"] is None else str(row._mapping["network"]),
        amount=None if row._mapping["amount"] is None else float(row._mapping["amount"]),
    )


def _map_purchase_lidl_row(row: Row) -> PurchaseLidlEntity:
    return PurchaseLidlEntity(
        purchase_id=str(row._mapping["purchase_id"]),
        lidlplus_discount=None if row._mapping["lidlplus_discount"] is None else float(row._mapping["lidlplus_discount"]),
        sticker_discount=None if row._mapping["sticker_discount"] is None else float(row._mapping["sticker_discount"]),
    )


def _map_purchase_rewe_row(row: Row) -> PurchaseReweEntity:
    return PurchaseReweEntity(
        purchase_id=str(row._mapping["purchase_id"]),
        rewe_bonus_amount=float(row._mapping["rewe_bonus_amount"]),
        rewe_bonus_total_amount=float(row._mapping["rewe_bonus_total_amount"]),
        rewe_bonus_discount=float(row._mapping["rewe_bonus_discount"]),
    )


class RetailerDomain:
    def __init__(self, connection: Connection) -> None:
        self.__connection = connection

    def find_by_code(self, code: str) -> RetailerEntity | None:
        stmt = (
            select(retailer_table.c.code, retailer_table.c.name, retailer_table.c.country)
            .where(retailer_table.c.code == code)
        )
        row = self.__connection.execute(stmt).fetchone()
        return None if row is None else _map_retailer_row(row)

    def insert(self, entity: RetailerEntity) -> None:
        self.__connection.execute(
            insert_stmt(retailer_table).values(
                code=entity.code,
                name=entity.name,
                country=entity.country,
            )
        )

    def update(self, entity: RetailerEntity) -> None:
        self.__connection.execute(
            retailer_table.update()
            .where(retailer_table.c.code == entity.code)
            .values(name=entity.name, country=entity.country)
        )

    def upsert(self, entity: RetailerEntity) -> None:
        existing = self.find_by_code(entity.code)
        if existing is None:
            self.insert(entity)
            return
        if existing == entity:
            return
        self.update(entity)


class StoreDomain:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    @staticmethod
    def _select_all() -> Select:
        return select(
            store_table.c.id,
            store_table.c.retailer_code,
            store_table.c.name,
            store_table.c.market,
            store_table.c.street,
            store_table.c.street_no,
            store_table.c.zip,
            store_table.c.city,
            store_table.c.hash,
        )

    def find_by_hash(self, store_hash: str) -> StoreEntity | None:
        stmt = self._select_all().where(store_table.c.hash == store_hash)
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else _map_store_row(row)

    def find_by_id(self, store_id: int) -> StoreEntity | None:
        stmt = self._select_all().where(store_table.c.id == store_id)
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else _map_store_row(row)

    def find_id_by_hash(self, store_hash: str) -> int | None:
        stmt = select(store_table.c.id).where(store_table.c.hash == store_hash)
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else int(row._mapping["id"])

    def insert(self, entity: StoreEntity) -> None:
        self.connection.execute(
            insert_stmt(store_table).values(
                retailer_code=entity.retailer_code,
                name=entity.name,
                market=entity.market,
                street=entity.street,
                street_no=entity.street_no,
                zip=entity.zip,
                city=entity.city,
                hash=entity.hash,
            )
        )

    def resolve_id(self, entity: StoreEntity) -> int | None:
        existing_id = self.find_id_by_hash(entity.hash)
        if existing_id is not None:
            return existing_id
        self.insert(entity)
        return self.find_id_by_hash(entity.hash)


class PurchaseDomain:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    @staticmethod
    def _select_all() -> Select:
        return select(
            purchase_table.c.id,
            purchase_table.c.store_id,
            purchase_table.c.purchase_date,
            purchase_table.c.bon_number,
            purchase_table.c.register_id,
            purchase_table.c.cashier,
            purchase_table.c.total_price,
            purchase_table.c.discount,
            purchase_table.c.saved_deposit,
            purchase_table.c.currency,
            purchase_table.c.source_file,
            purchase_table.c.hash,
        )

    def find_by_id(self, purchase_id: str) -> PurchaseEntity | None:
        stmt = self._select_all().where(purchase_table.c.id == purchase_id)
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else _map_purchase_row(row)

    def find_hash_by_id(self, purchase_id: str) -> str | None:
        stmt = select(purchase_table.c.hash).where(purchase_table.c.id == purchase_id)
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else str(row._mapping["hash"])

    def insert(self, entity: PurchaseEntity) -> None:
        self.connection.execute(
            insert_stmt(purchase_table).values(
                id=entity.id,
                store_id=entity.store_id,
                purchase_date=entity.purchase_date,
                bon_number=entity.bon_number,
                register_id=entity.register_id,
                cashier=entity.cashier,
                total_price=entity.total_price,
                discount=entity.discount,
                saved_deposit=entity.saved_deposit,
                currency=entity.currency,
                source_file=entity.source_file,
                hash=entity.hash,
            )
        )

    def replace(self, entity: PurchaseEntity) -> None:
        """Update an existing purchase row without triggering ON DELETE CASCADE.

        Using UPDATE instead of INSERT OR REPLACE because REPLACE internally
        does DELETE + INSERT, which triggers CASCADE and destroys child rows.
        """
        self.connection.execute(
            purchase_table.update()
            .where(purchase_table.c.id == entity.id)
            .values(
                store_id=entity.store_id,
                purchase_date=entity.purchase_date,
                bon_number=entity.bon_number,
                register_id=entity.register_id,
                cashier=entity.cashier,
                total_price=entity.total_price,
                discount=entity.discount,
                saved_deposit=entity.saved_deposit,
                currency=entity.currency,
                source_file=entity.source_file,
                hash=entity.hash,
            )
        )

    def persist(self, entity: PurchaseEntity) -> str | None:
        existing_hash = self.find_hash_by_id(entity.id)
        if existing_hash == entity.hash:
            return None
        if existing_hash is None:
            self.insert(entity)
            return "created"
        self.replace(entity)
        return "updated"

    def find_ids_by_retailer(self, retailer_code: str) -> set[str]:
        stmt = (
            select(purchase_table.c.id)
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(store_table.c.retailer_code == retailer_code.lower())
        )
        rows = self.connection.execute(stmt).fetchall()
        return {str(row._mapping["id"]) for row in rows}

    def find_by_retailer(self, retailer_code: str) -> list[PurchaseEntity]:
        stmt = (
            self._select_all()
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(store_table.c.retailer_code == retailer_code.lower())
            .order_by(purchase_table.c.purchase_date.desc(), purchase_table.c.id)
        )
        rows = self.connection.execute(stmt).fetchall()
        return [_map_purchase_row(row) for row in rows]

    def count_by_retailer(self, retailer_code: str) -> int:
        stmt = (
            select(func.count(purchase_table.c.id))
            .join(store_table, store_table.c.id == purchase_table.c.store_id)
            .where(store_table.c.retailer_code == retailer_code)
        )
        row = self.connection.execute(stmt).fetchone()
        return 0 if row is None else int(row[0])


class PurchaseItemDomain:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def insert_many(self, entities: Sequence[PurchaseItemEntity]) -> None:
        rows = [
            {
                "purchase_id": entity.purchase_id,
                "position": entity.position,
                "name": entity.name,
                "quantity": entity.quantity,
                "unit": entity.unit,
                "price": entity.price,
            }
            for entity in entities
        ]
        if not rows:
            return
        self.connection.execute(insert_stmt(purchase_item_table), rows)

    def find_by_purchase_id(self, purchase_id: str) -> list[PurchaseItemEntity]:
        stmt = (
            select(
                purchase_item_table.c.id,
                purchase_item_table.c.purchase_id,
                purchase_item_table.c.position,
                purchase_item_table.c.name,
                purchase_item_table.c.quantity,
                purchase_item_table.c.unit,
                purchase_item_table.c.price,
            )
            .where(purchase_item_table.c.purchase_id == purchase_id)
        )
        rows = self.connection.execute(stmt).fetchall()
        return [_map_purchase_item_row(row) for row in rows]

    def find_purchase_ids_by_item_name(self, name: str) -> list[str]:
        stmt = (
            select(purchase_item_table.c.purchase_id)
            .distinct()
            .where(func.upper(purchase_item_table.c.name) == func.upper(name))
        )
        rows = self.connection.execute(stmt).fetchall()
        return [str(row._mapping["purchase_id"]) for row in rows]


class PaymentMethodDomain:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def insert_many(self, entities: Sequence[PaymentMethodEntity]) -> None:
        rows = [
            {
                "purchase_id": entity.purchase_id,
                "position": entity.position,
                "method": entity.method,
                "network": entity.network,
                "amount": entity.amount,
            }
            for entity in entities
        ]
        if not rows:
            return
        self.connection.execute(insert_stmt(payment_method_table), rows)

    def find_by_purchase_id(self, purchase_id: str) -> list[PaymentMethodEntity]:
        stmt = (
            select(
                payment_method_table.c.id,
                payment_method_table.c.purchase_id,
                payment_method_table.c.position,
                payment_method_table.c.method,
                payment_method_table.c.network,
                payment_method_table.c.amount,
            )
            .where(payment_method_table.c.purchase_id == purchase_id)
        )
        rows = self.connection.execute(stmt).fetchall()
        return [_map_payment_method_row(row) for row in rows]


class PurchaseLidlDomain:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def insert(self, entity: PurchaseLidlEntity) -> None:
        self.connection.execute(
            insert_stmt(purchase_lidl_table).values(
                purchase_id=entity.purchase_id,
                lidlplus_discount=entity.lidlplus_discount,
                sticker_discount=entity.sticker_discount,
            )
        )

    def find_by_purchase_id(self, purchase_id: str) -> PurchaseLidlEntity | None:
        stmt = (
            select(
                purchase_lidl_table.c.purchase_id,
                purchase_lidl_table.c.lidlplus_discount,
                purchase_lidl_table.c.sticker_discount,
            )
            .where(purchase_lidl_table.c.purchase_id == purchase_id)
        )
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else _map_purchase_lidl_row(row)


class PurchaseReweDomain:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def insert(self, entity: PurchaseReweEntity) -> None:
        self.connection.execute(
            insert_stmt(purchase_rewe_table).values(
                purchase_id=entity.purchase_id,
                rewe_bonus_amount=entity.rewe_bonus_amount,
                rewe_bonus_total_amount=entity.rewe_bonus_total_amount,
                rewe_bonus_discount=entity.rewe_bonus_discount,
            )
        )

    def find_by_purchase_id(self, purchase_id: str) -> PurchaseReweEntity | None:
        stmt = (
            select(
                purchase_rewe_table.c.purchase_id,
                purchase_rewe_table.c.rewe_bonus_amount,
                purchase_rewe_table.c.rewe_bonus_total_amount,
                purchase_rewe_table.c.rewe_bonus_discount,
            )
            .where(purchase_rewe_table.c.purchase_id == purchase_id)
        )
        row = self.connection.execute(stmt).fetchone()
        return None if row is None else _map_purchase_rewe_row(row)
