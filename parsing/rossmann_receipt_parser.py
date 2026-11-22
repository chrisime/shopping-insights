"""Parse Rossmann anybill receipt JSON into the shared receipt schema.

Anybill receipts deliver full item lines in ``data.lines`` (type ``Default``)
with name, quantity, unit, and price. Discount lines and text lines are not
imported as items. The seller address in ``head.seller.address`` maps onto the
shared address schema.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import re

from shared.receipt_schema import ReceiptCoupon, ReceiptData, build_receipt_schema

_LINE_TYPE_DEFAULT = "Default"
_COUPON_LABEL = re.compile(r"\bcoupon(?:s|aktion)?\b", re.IGNORECASE)
_APP_COUPON_LABEL = re.compile(r"\bapp[\s\-\u2010-\u2015]+coupons?\b", re.IGNORECASE)
_BASKET_COUPON_LABEL = re.compile(
    r"^\s*(?:10\s*%\s+couponaktion\b|(?:app[- ]+)?coupon\s+10\s*%\s+(?:auf\s+alles|auf\s+den\s+gesamten\s+einkauf)\b)",
    re.IGNORECASE,
)
_PRODUCT_COUPON_LABEL = re.compile(
    r"^\s*(?:app[- ]+)?coupon\s+(?:(?:\d+\s*(?:%|€)|\d+\s*\+\s*\d+)\s+)?"
    r"(?!auf\s+(?:alles|den\s+gesamten\s+einkauf)\b)(?:auf\s+)?"
    r"(?!aktion\b|angebot\b|rabatt\b)[^\W\d_]",
    re.IGNORECASE,
)


def parse_rossmann_receipt(data: dict) -> ReceiptData:
    """Parse an anybill receipt JSON dict into the normalized receipt structure."""
    receipt_id = str(data.get("id") or "").strip()
    head = data.get("head") or {}
    body = data.get("data") or {}
    purchase_date = _parse_date(head.get("date"))
    if not receipt_id or not purchase_date:
        raise ValueError("Rossmann-Beleg konnte nicht eindeutig identifiziert werden")

    seller = head.get("seller") or {}
    address = _normalize_address(seller.get("address") or {})
    discount = _receipt_discount(body)
    coupon_discount, app_coupon_discount, basket_coupon, product_coupon, coupons = _coupon_discounts(body, discount)

    return build_receipt_schema(
        receipt_id=receipt_id,
        retailer="rossmann",
        purchase_date=purchase_date,
        store=_optional_text(seller.get("name")),
        address=address,
        total_price=body.get("fullAmountInclVat"),
        discount=discount,
        rossmann_coupons=coupons,
        rossmann_coupon_discount=coupon_discount,
        rossmann_app_coupon_discount=app_coupon_discount,
        rossmann_basket_coupon_discount=basket_coupon,
        rossmann_product_coupon_discount=product_coupon,
        currency=str(body.get("currency") or "EUR"),
        items=_build_items(body.get("lines") or []),
        source_file=receipt_id,
    )


def _receipt_discount(body: dict) -> float:
    original_total = _money(body.get("fullAmountInclVatBeforeDiscounts"))
    paid_total = _money(body.get("fullAmountInclVat"))
    if original_total is not None and paid_total is not None:
        return float(round(original_total - paid_total, 2))

    # These representations can describe the same discounts. Use one source.
    receipt_amounts = _discount_amounts(body.get("discounts") or [])
    if receipt_amounts:
        return float(round(sum(receipt_amounts), 2))

    lines = [line for line in body.get("lines") or [] if isinstance(line, dict)]
    item_amounts = [
        amount for line in lines if line.get("type") in (None, _LINE_TYPE_DEFAULT)
        for amount in _discount_amounts(line.get("discounts") or [])
    ]
    if item_amounts:
        return float(round(sum(item_amounts), 2))

    discount_lines = [line for line in lines if line.get("type") == "Discount"]
    return float(round(-sum(_discount_amounts(discount_lines)), 2))


def _discount_amounts(entries: list) -> list[Decimal]:
    return [
        amount for entry in entries if isinstance(entry, dict)
        if (amount := _money(entry.get("fullAmountInclVat"))) is not None
    ]


def _money(value: object) -> Decimal | None:
    if not isinstance(value, (Decimal, float, int)) or isinstance(value, bool):
        return None
    amount = Decimal(str(value))
    return amount if amount.is_finite() else None


def _coupon_discounts(body: dict, total_discount: float) -> tuple[float | None, float | None, float | None, float | None, list[ReceiptCoupon]]:
    """Classify coupon amounts by redemption channel and scope independently."""
    linked_amounts: dict[str, Decimal] = defaultdict(Decimal)
    lines = [line for line in body.get("lines") or [] if isinstance(line, dict)]
    definitions = {
        entry["id"]: entry
        for entry in body.get("discounts") or []
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    for line in lines:
        if line.get("type") not in (None, _LINE_TYPE_DEFAULT):
            continue
        for entry in line.get("discounts") or []:
            if not isinstance(entry, dict) or not isinstance(entry.get("discountId"), str):
                continue
            amount = _money(entry.get("fullAmountInclVat"))
            if amount is not None:
                linked_amounts[entry["discountId"]] += amount

    named_amounts = [
        (
            " ".join(str(entry.get(key) or "") for key in ("name", "additionalText")),
            linked_amounts[coupon_id] if coupon_id in linked_amounts else _money(entry.get("fullAmountInclVat")),
        )
        for coupon_id, entry in definitions.items()
    ]
    if not definitions:
        named_amounts = [
            (str(line.get("text") or ""), -amount)
            for line in lines
            if line.get("type") == "Discount" and (amount := _money(line.get("fullAmountInclVat"))) is not None
        ]

    coupon_details: list[ReceiptCoupon] = []
    coupons: list[Decimal] = []
    app_coupons: list[Decimal] = []
    basket_coupons: list[Decimal] = []
    product_coupons: list[Decimal] = []
    for label, amount in named_amounts:
        if amount is None or not _COUPON_LABEL.search(label):
            continue
        target = app_coupons if _APP_COUPON_LABEL.search(label) else coupons
        target.append(amount)
        coupon_details.append({"name": label.strip(), "savings": float(round(amount, 2))})
        if _BASKET_COUPON_LABEL.search(label):
            basket_coupons.append(amount)
        elif _PRODUCT_COUPON_LABEL.search(label):
            product_coupons.append(amount)

    coupon_sum = round(sum(coupons, Decimal(0)), 2)
    app_coupon_sum = round(sum(app_coupons, Decimal(0)), 2)
    receipt_total = Decimal(str(total_discount))
    # Keep inconsistent amounts in the unclassified balance.
    if abs(coupon_sum + app_coupon_sum) > abs(receipt_total) or (
        coupon_sum * receipt_total < 0 or app_coupon_sum * receipt_total < 0
    ):
        return None, None, None, None, []
    return (
        float(coupon_sum) if coupons else None,
        float(app_coupon_sum) if app_coupons else None,
        float(round(sum(basket_coupons), 2)) if basket_coupons else None,
        float(round(sum(product_coupons), 2)) if product_coupons else None,
        coupon_details,
    )


def _build_items(lines: list) -> list[dict]:
    """Extract item lines (type ``Default``) into normalized items."""
    items: list[dict] = []
    default_line_type = _LINE_TYPE_DEFAULT
    for index, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            continue
        if line.get("type") not in (None, default_line_type):
            continue
        line_item = line.get("item") or {}
        name = _optional_text(line.get("text")) or _optional_text(line_item.get("name"))
        if not name:
            continue
        quantity = line_item.get("quantity")
        quantity_measure = line_item.get("quantityMeasure")
        unit = _normalize_unit(quantity_measure)
        price = line_item.get("pricePerUnitBeforeDiscounts")
        original_line_total = _money(line.get("fullAmountInclVatBeforeDiscounts"))
        units = _money(quantity) if quantity is not None else Decimal(1)
        if price is None and original_line_total is None:
            paid_line_total = _money(line.get("fullAmountInclVat"))
            discounts = _discount_amounts(line.get("discounts") or [])
            if paid_line_total is not None and discounts:
                original_line_total = paid_line_total + sum(discounts)
        if price is None and original_line_total is not None and units:
            price = float(original_line_total / units)
        if price is None:
            price = line_item.get("pricePerUnit")
        if price is None:
            price = line.get("fullAmountInclVat")

        items.append(
            {
                "position": index,
                "name": name,
                "price": price,
                "quantity": quantity if quantity is not None else 1,
                "unit": unit,
            }
        )
    return items


def _normalize_unit(measure: object) -> str:
    mapping = {
        "Count": "stk",
        "Kilogram": "kg",
        "Gram": "g",
        "Liter": "l",
        "Meters": "m",
    }
    if not measure:
        return "stk"
    return mapping.get(str(measure), str(measure).lower())


def _parse_date(value: object) -> str | None:
    """Extract an ISO date (yyyy-mm-dd) from an anybill datetime string."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:10] if len(text) >= 10 else None


def _normalize_address(address: dict) -> dict:
    return {
        "street": _optional_text(address.get("street")),
        "street_no": None,
        "zip": _optional_text(address.get("postalCode")),
        "city": _optional_text(address.get("city")),
    }


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
