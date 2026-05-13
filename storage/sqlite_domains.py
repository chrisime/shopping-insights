"""PyPika-based SQLite domains for receipt persistence."""

from __future__ import annotations

import sqlite3
from typing import Sequence

from pypika import Parameter, Table, functions as fn
from pypika.dialects import SQLLiteQuery

from .sqlite_entities import (
    PaymentMethodEntity,
    PurchaseEntity,
    PurchaseItemEntity,
    PurchaseLidlEntity,
    PurchaseReweEntity,
    RetailerEntity,
    StoreEntity,
)

RETAILER_TABLE = Table("retailer")
STORE_TABLE = Table("store")
PURCHASE_TABLE = Table("purchase")
PURCHASE_ITEM_TABLE = Table("purchase_item")
PAYMENT_METHOD_TABLE = Table("payment_method")
PURCHASE_LIDL_TABLE = Table("purchase_lidl")
PURCHASE_REWE_TABLE = Table("purchase_rewe")


class RetailerDomain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.__connection = connection

    def find_by_code(self, code: str) -> RetailerEntity | None:
        row = self.__connection.execute(
            (
                SQLLiteQuery.from_(RETAILER_TABLE)
                .select(RETAILER_TABLE.code, RETAILER_TABLE.name, RETAILER_TABLE.country)
                .where(RETAILER_TABLE.code == Parameter("?"))
            ).get_sql(),
            (code,),
        ).fetchone()

        if row is None:
            return None
        return RetailerEntity(
            code=str(row["code"]),
            name=str(row["name"]),
            country=str(row["country"]),
        )

    def insert(self, entity: RetailerEntity) -> None:
        self.__connection.execute(
            (
                SQLLiteQuery.into(RETAILER_TABLE)
                .columns(RETAILER_TABLE.code, RETAILER_TABLE.name, RETAILER_TABLE.country)
                .insert(Parameter("?"), Parameter("?"), Parameter("?"))
            ).get_sql(),
            (entity.code, entity.name, entity.country),
        )

    def update(self, entity: RetailerEntity) -> None:
        self.__connection.execute(
            (
                SQLLiteQuery.update(RETAILER_TABLE)
                .set(RETAILER_TABLE.name, Parameter("?"))
                .set(RETAILER_TABLE.country, Parameter("?"))
                .where(RETAILER_TABLE.code == Parameter("?"))
            ).get_sql(),
            (entity.name, entity.country, entity.code),
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
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def find_by_hash(self, store_hash: str) -> StoreEntity | None:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(STORE_TABLE)
                .select(
                    STORE_TABLE.id,
                    STORE_TABLE.retailer_code,
                    STORE_TABLE.name,
                    STORE_TABLE.street,
                    STORE_TABLE.street_no,
                    STORE_TABLE.zip,
                    STORE_TABLE.city,
                    STORE_TABLE.hash,
                )
                .where(STORE_TABLE.hash == Parameter("?"))
            ).get_sql(),
            (store_hash,),
        ).fetchone()

        if row is None:
            return None

        return StoreEntity(
            id=int(row["id"]),
            retailer_code=str(row["retailer_code"]),
            name=str(row["name"]),
            street=str(row["street"]),
            street_no=str(row["street_no"]),
            zip=str(row["zip"]),
            city=str(row["city"]),
            hash=str(row["hash"]),
        )

    def find_id_by_hash(self, store_hash: str) -> int | None:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(STORE_TABLE)
                .select(STORE_TABLE.id)
                .where(STORE_TABLE.hash == Parameter("?"))
            ).get_sql(),
            (store_hash,),
        ).fetchone()
        return None if row is None else int(row["id"])

    def insert(self, entity: StoreEntity) -> None:
        self.connection.execute(
            (
                SQLLiteQuery.into(STORE_TABLE)
                .columns(
                    STORE_TABLE.retailer_code,
                    STORE_TABLE.name,
                    STORE_TABLE.street,
                    STORE_TABLE.street_no,
                    STORE_TABLE.zip,
                    STORE_TABLE.city,
                    STORE_TABLE.hash,
                )
                .insert(
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                )
            ).get_sql(),
            (
                entity.retailer_code,
                entity.name,
                entity.street,
                entity.street_no,
                entity.zip,
                entity.city,
                entity.hash,
            ),
        )

    def resolve_id(self, entity: StoreEntity) -> int | None:
        existing_id = self.find_id_by_hash(entity.hash)
        if existing_id is not None:
            return existing_id
        self.insert(entity)
        return self.find_id_by_hash(entity.hash)


class PurchaseDomain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def find_by_id(self, purchase_id: str) -> PurchaseEntity | None:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_TABLE)
                .select(
                    PURCHASE_TABLE.id,
                    PURCHASE_TABLE.store_id,
                    PURCHASE_TABLE.purchase_date,
                    PURCHASE_TABLE.market,
                    PURCHASE_TABLE.register_id,
                    PURCHASE_TABLE.cashier,
                    PURCHASE_TABLE.total_price,
                    PURCHASE_TABLE.amount_saved,
                    PURCHASE_TABLE.saved_deposit,
                    PURCHASE_TABLE.currency,
                    PURCHASE_TABLE.source_file,
                    PURCHASE_TABLE.hash,
                )
                .where(PURCHASE_TABLE.id == Parameter("?"))
            ).get_sql(),
            (purchase_id,),
        ).fetchone()
        if row is None:
            return None
        return PurchaseEntity(
            id=str(row["id"]),
            store_id=None if row["store_id"] is None else int(row["store_id"]),
            purchase_date=str(row["purchase_date"]),
            market=None if row["market"] is None else str(row["market"]),
            register_id=None if row["register_id"] is None else str(row["register_id"]),
            cashier=None if row["cashier"] is None else str(row["cashier"]),
            total_price=None if row["total_price"] is None else float(row["total_price"]),
            amount_saved=float(row["amount_saved"]),
            saved_deposit=float(row["saved_deposit"]),
            currency=str(row["currency"]),
            source_file=None if row["source_file"] is None else str(row["source_file"]),
            hash=str(row["hash"]),
        )

    def find_hash_by_id(self, purchase_id: str) -> str | None:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_TABLE)
                .select(PURCHASE_TABLE.hash)
                .where(PURCHASE_TABLE.id == Parameter("?"))
            ).get_sql(),
            (purchase_id,),
        ).fetchone()
        return None if row is None else str(row["hash"])

    def insert(self, entity: PurchaseEntity) -> None:
        self.connection.execute(
            (
                SQLLiteQuery.into(PURCHASE_TABLE)
                .columns(
                    PURCHASE_TABLE.id,
                    PURCHASE_TABLE.store_id,
                    PURCHASE_TABLE.purchase_date,
                    PURCHASE_TABLE.market,
                    PURCHASE_TABLE.register_id,
                    PURCHASE_TABLE.cashier,
                    PURCHASE_TABLE.total_price,
                    PURCHASE_TABLE.amount_saved,
                    PURCHASE_TABLE.saved_deposit,
                    PURCHASE_TABLE.currency,
                    PURCHASE_TABLE.source_file,
                    PURCHASE_TABLE.hash,
                )
                .insert(
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                )
            ).get_sql(),
            (
                entity.id,
                entity.store_id,
                entity.purchase_date,
                entity.market,
                entity.register_id,
                entity.cashier,
                entity.total_price,
                entity.amount_saved,
                entity.saved_deposit,
                entity.currency,
                entity.source_file,
                entity.hash,
            ),
        )

    def replace(self, entity: PurchaseEntity) -> None:
        self.connection.execute(
            (
                SQLLiteQuery.into(PURCHASE_TABLE)
                .columns(
                    PURCHASE_TABLE.id,
                    PURCHASE_TABLE.store_id,
                    PURCHASE_TABLE.purchase_date,
                    PURCHASE_TABLE.market,
                    PURCHASE_TABLE.register_id,
                    PURCHASE_TABLE.cashier,
                    PURCHASE_TABLE.total_price,
                    PURCHASE_TABLE.amount_saved,
                    PURCHASE_TABLE.saved_deposit,
                    PURCHASE_TABLE.currency,
                    PURCHASE_TABLE.source_file,
                    PURCHASE_TABLE.hash,
                )
                .replace(
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                )
            ).get_sql(),
            (
                entity.id,
                entity.store_id,
                entity.purchase_date,
                entity.market,
                entity.register_id,
                entity.cashier,
                entity.total_price,
                entity.amount_saved,
                entity.saved_deposit,
                entity.currency,
                entity.source_file,
                entity.hash,
            ),
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
        rows = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_TABLE)
                .join(STORE_TABLE)
                .on(STORE_TABLE.id == PURCHASE_TABLE.store_id)
                .select(PURCHASE_TABLE.id)
                .where(STORE_TABLE.retailer_code == Parameter("?"))
            ).get_sql(),
            (retailer_code,),
        ).fetchall()
        return {str(row["id"]) for row in rows}

    def count_by_retailer(self, retailer_code: str) -> int:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_TABLE)
                .join(STORE_TABLE)
                .on(STORE_TABLE.id == PURCHASE_TABLE.store_id)
                .select(fn.Count(PURCHASE_TABLE.id))
                .where(STORE_TABLE.retailer_code == Parameter("?"))
            ).get_sql(),
            (retailer_code,),
        ).fetchone()
        return 0 if row is None else int(row[0])


class PurchaseItemDomain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def insert_many(self, entities: Sequence[PurchaseItemEntity]) -> None:
        rows = [
            (
                entity.purchase_id,
                entity.position,
                entity.name,
                entity.quantity,
                entity.unit,
                entity.price,
            )
            for entity in entities
        ]
        if not rows:
            return
        self.connection.executemany(
            (
                SQLLiteQuery.into(PURCHASE_ITEM_TABLE)
                .columns(
                    PURCHASE_ITEM_TABLE.purchase_id,
                    PURCHASE_ITEM_TABLE.position,
                    PURCHASE_ITEM_TABLE.name,
                    PURCHASE_ITEM_TABLE.quantity,
                    PURCHASE_ITEM_TABLE.unit,
                    PURCHASE_ITEM_TABLE.price,
                )
                .insert(
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                )
            ).get_sql(),
            rows,
        )

    def find_by_purchase_id(self, purchase_id: str) -> list[PurchaseItemEntity]:
        rows = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_ITEM_TABLE)
                .select(
                    PURCHASE_ITEM_TABLE.id,
                    PURCHASE_ITEM_TABLE.purchase_id,
                    PURCHASE_ITEM_TABLE.position,
                    PURCHASE_ITEM_TABLE.name,
                    PURCHASE_ITEM_TABLE.quantity,
                    PURCHASE_ITEM_TABLE.unit,
                    PURCHASE_ITEM_TABLE.price,
                )
                .where(PURCHASE_ITEM_TABLE.purchase_id == Parameter("?"))
            ).get_sql(),
            (purchase_id,),
        ).fetchall()
        return [
            PurchaseItemEntity(
                id=int(row["id"]),
                purchase_id=str(row["purchase_id"]),
                position=int(row["position"]),
                name=str(row["name"]),
                quantity=float(row["quantity"]),
                unit=str(row["unit"]),
                price=float(row["price"]),
            )
            for row in rows
        ]


class PaymentMethodDomain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def insert_many(self, entities: Sequence[PaymentMethodEntity]) -> None:
        rows = [
            (
                entity.purchase_id,
                entity.position,
                entity.method,
                entity.network,
                entity.amount,
            )
            for entity in entities
        ]
        if not rows:
            return
        self.connection.executemany(
            (
                SQLLiteQuery.into(PAYMENT_METHOD_TABLE)
                .columns(
                    PAYMENT_METHOD_TABLE.purchase_id,
                    PAYMENT_METHOD_TABLE.position,
                    PAYMENT_METHOD_TABLE.method,
                    PAYMENT_METHOD_TABLE.network,
                    PAYMENT_METHOD_TABLE.amount,
                )
                .insert(
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                    Parameter("?"),
                )
            ).get_sql(),
            rows,
        )

    def find_by_purchase_id(self, purchase_id: str) -> list[PaymentMethodEntity]:
        rows = self.connection.execute(
            (
                SQLLiteQuery.from_(PAYMENT_METHOD_TABLE)
                .select(
                    PAYMENT_METHOD_TABLE.id,
                    PAYMENT_METHOD_TABLE.purchase_id,
                    PAYMENT_METHOD_TABLE.position,
                    PAYMENT_METHOD_TABLE.method,
                    PAYMENT_METHOD_TABLE.network,
                    PAYMENT_METHOD_TABLE.amount,
                )
                .where(PAYMENT_METHOD_TABLE.purchase_id == Parameter("?"))
            ).get_sql(),
            (purchase_id,),
        ).fetchall()
        return [
            PaymentMethodEntity(
                id=int(row["id"]),
                purchase_id=str(row["purchase_id"]),
                position=int(row["position"]),
                method=str(row["method"]),
                network=None if row["network"] is None else str(row["network"]),
                amount=None if row["amount"] is None else float(row["amount"]),
            )
            for row in rows
        ]


class PurchaseLidlDomain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def insert(self, entity: PurchaseLidlEntity) -> None:
        self.connection.execute(
            (
                SQLLiteQuery.into(PURCHASE_LIDL_TABLE)
                .columns(
                    PURCHASE_LIDL_TABLE.purchase_id,
                    PURCHASE_LIDL_TABLE.lidlplus_amount_saved,
                    PURCHASE_LIDL_TABLE.sticker_discount_amount,
                )
                .insert(Parameter("?"), Parameter("?"), Parameter("?"))
            ).get_sql(),
            (
                entity.purchase_id,
                entity.lidlplus_amount_saved,
                entity.sticker_discount_amount,
            ),
        )

    def find_by_purchase_id(self, purchase_id: str) -> PurchaseLidlEntity | None:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_LIDL_TABLE)
                .select(
                    PURCHASE_LIDL_TABLE.purchase_id,
                    PURCHASE_LIDL_TABLE.lidlplus_amount_saved,
                    PURCHASE_LIDL_TABLE.sticker_discount_amount,
                )
                .where(PURCHASE_LIDL_TABLE.purchase_id == Parameter("?"))
            ).get_sql(),
            (purchase_id,),
        ).fetchone()
        if row is None:
            return None
        return PurchaseLidlEntity(
            purchase_id=str(row["purchase_id"]),
            lidlplus_amount_saved=None if row["lidlplus_amount_saved"] is None else float(row["lidlplus_amount_saved"]),
            sticker_discount_amount=None if row["sticker_discount_amount"] is None else float(row["sticker_discount_amount"]),
        )


class PurchaseReweDomain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def insert(self, entity: PurchaseReweEntity) -> None:
        self.connection.execute(
            (
                SQLLiteQuery.into(PURCHASE_REWE_TABLE)
                .columns(
                    PURCHASE_REWE_TABLE.purchase_id,
                    PURCHASE_REWE_TABLE.rewe_bonus_amount,
                    PURCHASE_REWE_TABLE.rewe_bonus_total_amount,
                    PURCHASE_REWE_TABLE.rewe_bonus_amount_saved,
                )
                .insert(Parameter("?"), Parameter("?"), Parameter("?"), Parameter("?"))
            ).get_sql(),
            (
                entity.purchase_id,
                entity.rewe_bonus_amount,
                entity.rewe_bonus_total_amount,
                entity.rewe_bonus_amount_saved,
            ),
        )

    def find_by_purchase_id(self, purchase_id: str) -> PurchaseReweEntity | None:
        row = self.connection.execute(
            (
                SQLLiteQuery.from_(PURCHASE_REWE_TABLE)
                .select(
                    PURCHASE_REWE_TABLE.purchase_id,
                    PURCHASE_REWE_TABLE.rewe_bonus_amount,
                    PURCHASE_REWE_TABLE.rewe_bonus_total_amount,
                    PURCHASE_REWE_TABLE.rewe_bonus_amount_saved,
                )
                .where(PURCHASE_REWE_TABLE.purchase_id == Parameter("?"))
            ).get_sql(),
            (purchase_id,),
        ).fetchone()
        if row is None:
            return None
        return PurchaseReweEntity(
            purchase_id=str(row["purchase_id"]),
            rewe_bonus_amount=float(row["rewe_bonus_amount"]),
            rewe_bonus_total_amount=float(row["rewe_bonus_total_amount"]),
            rewe_bonus_amount_saved=float(row["rewe_bonus_amount_saved"]),
        )
