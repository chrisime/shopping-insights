"""Typed DTOs for normalized receipts and mapping helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AddressDTO:
    street: str
    street_no: str
    zip: str
    city: str


@dataclass(frozen=True)
class ReceiptItemDTO:
    position: int
    name: str
    quantity: float | int | None
    unit: str
    price: float | int | None


@dataclass(frozen=True)
class PaymentMethodDTO:
    position: int
    method: str
    network: str | None
    amount: float | None


@dataclass(frozen=True)
class ReceiptDTO:
    id: str
    retailer: str
    purchase_date: str
    store: str
    address: AddressDTO
    market: str | None
    register_id: str | None
    cashier: str | None
    total_price: float | None
    amount_saved: float
    saved_deposit: float
    currency: str
    source_file: str | None
    payload_hash: str
    items: tuple[ReceiptItemDTO, ...] = field(default_factory=tuple)
    payment_methods: tuple[PaymentMethodDTO, ...] = field(default_factory=tuple)
    lidlplus_amount_saved: float | None = None
    sticker_discount_amount: float | None = None
    rewe_bonus_amount: float | None = None
    rewe_bonus_total_amount: float | None = None
    rewe_bonus_amount_saved: float | None = None


def receipt_dict_to_dto(receipt_data: Mapping[str, Any], retailer: str | None = None) -> ReceiptDTO:
    """Build a typed receipt DTO from a normalized receipt dictionary."""
    address = dict(receipt_data.get("address") or {})
    resolved_retailer = str(retailer or receipt_data.get("retailer") or "").strip().lower()

    return ReceiptDTO(
        id=_to_text(receipt_data.get("id") or receipt_data.get("url")),
        retailer=resolved_retailer,
        purchase_date=_to_text(receipt_data.get("purchase_date")),
        store=_to_text(receipt_data.get("store")),
        address=AddressDTO(
            street=_to_text(address.get("street")),
            street_no=_to_text(address.get("street_no")),
            zip=_to_text(address.get("zip")),
            city=_to_text(address.get("city")),
        ),
        market=_to_optional_text(receipt_data.get("market")),
        register_id=_to_optional_text(receipt_data.get("register")),
        cashier=_to_optional_text(receipt_data.get("cashier")),
        total_price=_to_optional_float(receipt_data.get("total_price")),
        amount_saved=_to_float_or_default(receipt_data.get("amount_saved"), 0.0),
        saved_deposit=_to_float_or_default(receipt_data.get("saved_deposit"), 0.0),
        currency=_to_text(receipt_data.get("currency") or "EUR"),
        source_file=_to_optional_text(receipt_data.get("source_file")),
        payload_hash=_to_text(receipt_data.get("payload_hash")),
        items=_build_items(receipt_data.get("items")),
        payment_methods=_build_payment_methods(receipt_data.get("payment_methods")),
        lidlplus_amount_saved=_to_optional_float(receipt_data.get("lidlplus_amount_saved")),
        sticker_discount_amount=_to_optional_float(receipt_data.get("sticker_discount_amount")),
        rewe_bonus_amount=_to_optional_float(receipt_data.get("rewe_bonus_amount")),
        rewe_bonus_total_amount=_to_optional_float(receipt_data.get("rewe_bonus_total_amount")),
        rewe_bonus_amount_saved=_to_optional_float(receipt_data.get("rewe_bonus_amount_saved")),
    )


def receipt_dto_to_dict(receipt: ReceiptDTO) -> dict[str, Any]:
    """Convert a receipt DTO into a schema-compatible dictionary."""
    return {
        "id": receipt.id,
        "retailer": receipt.retailer,
        "purchase_date": receipt.purchase_date,
        "store": receipt.store,
        "address": {
            "street": receipt.address.street,
            "street_no": receipt.address.street_no,
            "zip": receipt.address.zip,
            "city": receipt.address.city,
        },
        "market": receipt.market,
        "register": receipt.register_id,
        "cashier": receipt.cashier,
        "total_price": receipt.total_price,
        "amount_saved": receipt.amount_saved,
        "saved_deposit": receipt.saved_deposit,
        "currency": receipt.currency,
        "source_file": receipt.source_file,
        "payload_hash": receipt.payload_hash,
        "lidlplus_amount_saved": receipt.lidlplus_amount_saved,
        "sticker_discount_amount": receipt.sticker_discount_amount,
        "rewe_bonus_amount": receipt.rewe_bonus_amount,
        "rewe_bonus_total_amount": receipt.rewe_bonus_total_amount,
        "rewe_bonus_amount_saved": receipt.rewe_bonus_amount_saved,
        "items": [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "price": item.price,
            }
            for item in receipt.items
        ],
        "payment_methods": [
            {
                "method": payment.method,
                "network": payment.network,
                "amount": payment.amount,
            }
            for payment in receipt.payment_methods
        ],
    }


def _build_items(raw_items: Any) -> tuple[ReceiptItemDTO, ...]:
    items: list[ReceiptItemDTO] = []
    for index, item in enumerate(raw_items or [], start=1):
        if not isinstance(item, Mapping):
            continue
        items.append(
            ReceiptItemDTO(
                position=index,
                name=_to_text(item.get("name")),
                quantity=_to_optional_number(item.get("quantity")),
                unit=_to_text(item.get("unit") or "stk"),
                price=_to_optional_number(item.get("price")),
            )
        )
    return tuple(items)


def _build_payment_methods(raw_methods: Any) -> tuple[PaymentMethodDTO, ...]:
    payment_methods: list[PaymentMethodDTO] = []
    for index, payment_method in enumerate(raw_methods or [], start=1):
        if not isinstance(payment_method, Mapping):
            continue
        payment_methods.append(
            PaymentMethodDTO(
                position=index,
                method=_to_text(payment_method.get("method")),
                network=_to_optional_text(payment_method.get("network")),
                amount=_to_optional_float(payment_method.get("amount")),
            )
        )
    return tuple(payment_methods)


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _to_optional_text(value: Any) -> str | None:
    text = _to_text(value)
    return text or None


def _to_optional_number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_float_or_default(value: Any, default: float) -> float:
    maybe_float = _to_optional_float(value)
    if maybe_float is None:
        return default
    return maybe_float

