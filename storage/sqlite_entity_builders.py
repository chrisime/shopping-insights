"""Builders for SQLite storage entities derived from normalized receipt data."""

from __future__ import annotations

import hashlib
import simplejson
from typing import Any

from shared.retailer_runtime import get_retailer_runtime
from shared.receipt_dto import ReceiptDTO

from .sqlite_entities import (
    PaymentMethodEntity,
    PurchaseEntity,
    PurchaseItemEntity,
    PurchaseLidlEntity,
    PurchaseReweEntity,
    RetailerEntity,
    StoreEntity,
)


def build_retailer_entity(retailer_code: str) -> RetailerEntity:
    retailer_runtime = get_retailer_runtime(retailer_code)
    if retailer_runtime is None:
        normalized_code = retailer_code.strip().lower()
        return RetailerEntity(normalized_code, normalized_code.upper(), "")

    return RetailerEntity(retailer_runtime.code, retailer_runtime.name, retailer_runtime.country)


def build_store_entity(receipt_dto: ReceiptDTO) -> StoreEntity:
    retailer_code = receipt_dto.retailer
    name = _to_text(receipt_dto.store)
    market = _to_optional_text(receipt_dto.market)
    street = _to_text(receipt_dto.address.street)
    street_no = _to_text(receipt_dto.address.street_no)
    zip_code = _to_text(receipt_dto.address.zip)
    city = _to_text(receipt_dto.address.city)

    if market:
        identity_payload = {
            "retailer_code": retailer_code,
            "market": market,
        }
    else:
        identity_payload = {
            "retailer_code": retailer_code,
            "name": name,
            "street": street,
            "street_no": street_no,
            "zip": zip_code,
            "city": city,
        }

    store_hash = _hash_text(
        simplejson.dumps(
            identity_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    return StoreEntity(
        retailer_code=retailer_code,
        name=name,
        market=market,
        street=street,
        street_no=street_no,
        zip=zip_code,
        city=city,
        hash=store_hash,
    )


def build_purchase_entity(receipt_dto: ReceiptDTO, store_id: int | None, payload_hash: str) -> PurchaseEntity:
    return PurchaseEntity(
        id=receipt_dto.id,
        store_id=store_id,
        purchase_date=receipt_dto.purchase_date,
        bon_number=receipt_dto.bon_number,
        register_id=receipt_dto.register_id,
        cashier=receipt_dto.cashier,
        total_price=receipt_dto.total_price,
        discount=receipt_dto.discount,
        saved_deposit=receipt_dto.saved_deposit,
        currency=receipt_dto.currency,
        source_file=receipt_dto.source_file,
        hash=payload_hash,
    )


def build_purchase_item_entities(receipt_dto: ReceiptDTO) -> list[PurchaseItemEntity]:
    purchase_id = receipt_dto.id
    return [
        PurchaseItemEntity(
            purchase_id=purchase_id,
            position=item.position,
            name=item.name,
            quantity=item.quantity if item.quantity is not None else 1,
            unit=item.unit or "stk",
            price=item.price if item.price is not None else 0,
        )
        for item in receipt_dto.items
    ]


def build_payment_method_entities(receipt_dto: ReceiptDTO) -> list[PaymentMethodEntity]:
    purchase_id = receipt_dto.id
    return [
        PaymentMethodEntity(
            purchase_id=purchase_id,
            position=payment_method.position,
            method=payment_method.method,
            network=payment_method.network,
            amount=payment_method.amount,
        )
        for payment_method in receipt_dto.payment_methods
    ]


def build_purchase_lidl_entity(receipt_dto: ReceiptDTO) -> PurchaseLidlEntity:
    return PurchaseLidlEntity(
        purchase_id=receipt_dto.id,
        lidlplus_discount=receipt_dto.lidlplus_discount,
        sticker_discount=receipt_dto.sticker_discount,
    )


def build_purchase_rewe_entity(receipt_dto: ReceiptDTO) -> PurchaseReweEntity:
    return PurchaseReweEntity(
        purchase_id=receipt_dto.id,
        rewe_bonus_amount=receipt_dto.rewe_bonus_amount or 0.0,
        rewe_bonus_total_amount=receipt_dto.rewe_bonus_total_amount or 0.0,
        rewe_bonus_discount=receipt_dto.rewe_bonus_discount or 0.0,
    )


def _hash_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_optional_text(value: Any) -> str | None:
    text = _to_text(value)
    return text or None

