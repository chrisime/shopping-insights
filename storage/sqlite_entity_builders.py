"""Builders for SQLite storage entities derived from normalized receipt data."""

from __future__ import annotations

import hashlib
import simplejson
from typing import Any

from config import get_retailer_runtime

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
        return RetailerEntity(
            code=normalized_code,
            name=normalized_code.upper(),
            country="",
        )

    return RetailerEntity(
        code=retailer_runtime.code,
        name=retailer_runtime.name,
        country=retailer_runtime.country,
    )


def build_store_entity(receipt_data: dict[str, Any]) -> StoreEntity:
    address = receipt_data.get("address") or {}
    retailer_code = str(receipt_data.get("retailer") or "").strip().lower()
    name = _to_text(receipt_data.get("store"))
    street = _to_text(address.get("street"))
    street_no = _to_text(address.get("street_no"))
    zip_code = _to_text(address.get("zip"))
    city = _to_text(address.get("city"))
    store_hash = _hash_text(
        simplejson.dumps(
            {
                "retailer_code": retailer_code,
                "name": name,
                "street": street,
                "street_no": street_no,
                "zip": zip_code,
                "city": city,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    return StoreEntity(
        retailer_code=retailer_code,
        name=name,
        street=street,
        street_no=street_no,
        zip=zip_code,
        city=city,
        hash=store_hash,
    )


def build_purchase_entity(
    receipt_data: dict[str, Any],
    store_id: int | None,
    payload_hash: str,
) -> PurchaseEntity:
    return PurchaseEntity(
        id=str(receipt_data["id"]),
        store_id=store_id,
        purchase_date=str(receipt_data.get("purchase_date") or ""),
        market=receipt_data.get("market"),
        register_id=receipt_data.get("register"),
        cashier=receipt_data.get("cashier"),
        total_price=receipt_data.get("total_price"),
        amount_saved=receipt_data.get("amount_saved") or 0.0,
        saved_deposit=receipt_data.get("saved_deposit") or 0.0,
        currency=str(receipt_data.get("currency") or "EUR"),
        source_file=receipt_data.get("source_file"),
        hash=payload_hash,
    )


def build_purchase_item_entities(receipt_data: dict[str, Any]) -> list[PurchaseItemEntity]:
    purchase_id = str(receipt_data["id"])
    return [
        PurchaseItemEntity(
            purchase_id=purchase_id,
            position=position,
            name=str(item.get("name") or ""),
            quantity=item.get("quantity") if item.get("quantity") is not None else 1,
            unit=str(item.get("unit") or "stk"),
            price=item.get("price") if item.get("price") is not None else 0,
        )
        for position, item in enumerate(receipt_data.get("items") or [], start=1)
    ]


def build_payment_method_entities(receipt_data: dict[str, Any]) -> list[PaymentMethodEntity]:
    purchase_id = str(receipt_data["id"])
    return [
        PaymentMethodEntity(
            purchase_id=purchase_id,
            position=position,
            method=str(payment_method.get("method") or ""),
            network=payment_method.get("network"),
            amount=payment_method.get("amount"),
        )
        for position, payment_method in enumerate(receipt_data.get("payment_methods") or [], start=1)
    ]


def build_purchase_lidl_entity(receipt_data: dict[str, Any]) -> PurchaseLidlEntity:
    return PurchaseLidlEntity(
        purchase_id=str(receipt_data["id"]),
        lidlplus_amount_saved=receipt_data.get("lidlplus_amount_saved"),
        sticker_discount_amount=receipt_data.get("sticker_discount_amount"),
    )


def build_purchase_rewe_entity(receipt_data: dict[str, Any]) -> PurchaseReweEntity:
    return PurchaseReweEntity(
        purchase_id=str(receipt_data["id"]),
        rewe_bonus_amount=receipt_data.get("rewe_bonus_amount") or 0.0,
        rewe_bonus_total_amount=receipt_data.get("rewe_bonus_total_amount") or 0.0,
        rewe_bonus_amount_saved=receipt_data.get("rewe_bonus_amount_saved") or 0.0,
    )


def _hash_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()

