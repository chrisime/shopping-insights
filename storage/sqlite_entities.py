"""Typed SQLite entities used by the storage domains."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetailerEntity:
    code: str
    name: str
    country: str


@dataclass(frozen=True)
class StoreEntity:
    retailer_code: str
    name: str
    market: str | None
    street: str
    street_no: str
    zip: str
    city: str
    hash: str
    id: int | None = None


@dataclass(frozen=True)
class PurchaseEntity:
    id: str
    store_id: int | None
    purchase_date: str
    register_id: str | None
    cashier: str | None
    total_price: float | None
    discount: float
    saved_deposit: float
    currency: str
    source_file: str | None
    hash: str


@dataclass(frozen=True)
class PurchaseItemEntity:
    purchase_id: str
    position: int
    name: str
    quantity: float | int
    unit: str
    price: float | int
    id: int | None = None


@dataclass(frozen=True)
class PaymentMethodEntity:
    purchase_id: str
    position: int
    method: str
    network: str | None
    amount: float | None
    id: int | None = None


@dataclass(frozen=True)
class PurchaseLidlEntity:
    purchase_id: str
    lidlplus_discount: float | None
    sticker_discount: float | None


@dataclass(frozen=True)
class PurchaseReweEntity:
    purchase_id: str
    rewe_bonus_amount: float
    rewe_bonus_total_amount: float
    rewe_bonus_discount: float
