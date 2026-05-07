"""Neutrale Schema-Helfer für normalisierte Receipt-Dictionaries."""

import re
from typing import Any, Dict, List, Optional

from shared.addresses import empty_address, normalize_address


MONEY_FIELDS = {
    "total_price",
    "total_price_no_saving",
    "amount_saved",
    "sticker_discount_amount",
    "saved_deposit",
    "lidlplus_amount_saved",
    "rewe_bonus_amount",
    "rewe_bonus_amount_saved",
    "rewe_bonus_total_amount",
}


DEFAULT_RECEIPT_FIELDS = {
    "total_price": None,
    "total_price_no_saving": None,
    "amount_saved": None,
    "sticker_discount_amount": None,
    "sticker_discount_pct": [],
    "saved_deposit": None,
    "lidlplus_amount_saved": None,
    "rewe_bonus_amount": None,
    "rewe_bonus_amount_saved": None,
    "rewe_bonus_total_amount": None,
    "address": empty_address(),
    "market": None,
    "register": None,
    "cashier": None,
    "source_file": None,
    "payment_methods": [],
    "items": [],
}


def build_receipt_schema(
    receipt_id: str,
    retailer: str,
    purchase_date: Optional[str],
    store: Optional[str],
    **overrides: Any,
) -> Dict[str, Any]:
    """Create a normalized receipt dict with shared core and optional fields."""
    receipt_data = {
        "id": receipt_id,
        "retailer": retailer,
        "purchase_date": _normalize_purchase_date(purchase_date, retailer),
        "store": store,
    }

    for key, value in DEFAULT_RECEIPT_FIELDS.items():
        if isinstance(value, list):
            receipt_data[key] = list(value)
        elif isinstance(value, dict):
            receipt_data[key] = dict(value)
        else:
            receipt_data[key] = value

    receipt_data.update(overrides)
    return receipt_data


def build_receipt_item(
    name: str,
    price: Any,
    quantity: Any = "1",
    unit: str = "stk",
) -> Dict[str, Any]:
    """Create a normalized receipt item dict."""
    normalized_unit = str(unit or "stk").strip().lower() or "stk"
    return {
        "name": name,
        "price": price,
        "quantity": _normalize_quantity_value(quantity, normalized_unit),
        "unit": normalized_unit,
    }


def normalize_receipt_schema(
    receipt_data: Dict[str, Any],
    retailer: Optional[str] = None,
) -> Dict[str, Any]:
    """Merge an existing receipt dict into the shared schema defaults."""
    resolved_retailer = retailer or receipt_data.get("retailer") or _infer_retailer(receipt_data)
    normalized = build_receipt_schema(
        receipt_id=receipt_data.get("id") or receipt_data.get("url") or "",
        retailer=resolved_retailer,
        purchase_date=receipt_data.get("purchase_date"),
        store=receipt_data.get("store"),
    )
    normalized.update(receipt_data)
    normalized["retailer"] = resolved_retailer
    normalized["purchase_date"] = _normalize_purchase_date(
        normalized.get("purchase_date"),
        resolved_retailer,
    )
    if normalized.get("payment_methods") is None:
        normalized["payment_methods"] = []
    if normalized.get("items") is None:
        normalized["items"] = []
    if normalized.get("sticker_discount_pct") is None:
        normalized["sticker_discount_pct"] = []
    normalized["address"] = normalize_address(normalized.get("address"))
    if resolved_retailer == "lidl" and normalized.get("lidlplus_amount_saved") is None:
        normalized["lidlplus_amount_saved"] = 0.0
    if resolved_retailer == "rewe" and normalized.get("rewe_bonus_amount") is None:
        normalized["rewe_bonus_amount"] = 0.0
    if resolved_retailer == "rewe" and normalized.get("rewe_bonus_amount_saved") is None:
        normalized["rewe_bonus_amount_saved"] = 0.0

    for field_name in MONEY_FIELDS:
        normalized[field_name] = _normalize_money_value(normalized.get(field_name))

    normalized["payment_methods"] = _normalize_payment_methods(normalized.get("payment_methods"))
    normalized["items"] = _normalize_items(normalized.get("items"))
    if resolved_retailer == "lidl":
        normalized["store"] = "lidl"
    return normalized


def _infer_retailer(receipt_data: Dict[str, Any]) -> str:
    """Infer the retailer from existing receipt fields when missing."""
    receipt_id = str(receipt_data.get("id") or receipt_data.get("url") or "")
    if receipt_id.startswith("rewe-"):
        return "rewe"
    return "lidl"


def _normalize_payment_methods(payment_methods: Any) -> List[Dict[str, Any]]:
    normalized_methods: List[Dict[str, Any]] = []
    for payment_method in payment_methods or []:
        if not isinstance(payment_method, dict):
            continue
        normalized_method = dict(payment_method)
        normalized_method["amount"] = _normalize_money_value(normalized_method.get("amount"))
        normalized_methods.append(normalized_method)
    return normalized_methods


def _normalize_items(items: Any) -> List[Dict[str, Any]]:
    normalized_items: List[Dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        normalized_item = dict(item)
        normalized_item["unit"] = str(normalized_item.get("unit") or "stk").strip().lower() or "stk"
        normalized_item["price"] = _normalize_money_value(normalized_item.get("price"))
        normalized_item["quantity"] = _normalize_quantity_value(
            normalized_item.get("quantity"),
            normalized_item["unit"],
        )
        normalized_items.append(normalized_item)
    return normalized_items


def _normalize_money_value(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)

    normalized = str(value).strip()
    if not normalized:
        return None

    match = re.search(r"-?\d+(?:[\.,]\d{1,2})?", normalized)
    if not match:
        return None

    number_text = match.group(0)
    if "," in number_text and "." in number_text:
        if number_text.rfind(",") > number_text.rfind("."):
            number_text = number_text.replace(".", "").replace(",", ".")
        else:
            number_text = number_text.replace(",", "")
    else:
        number_text = number_text.replace(",", ".")

    try:
        return round(float(number_text), 2)
    except ValueError:
        return None


def _normalize_quantity_value(value: Any, unit: str) -> Any:
    numeric_value = _parse_numeric_value(value)
    if numeric_value is None:
        return None
    if unit == "kg":
        return round(numeric_value, 3)
    return int(round(numeric_value))


def _parse_numeric_value(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).strip()
    if not normalized:
        return None

    match = re.search(r"-?\d+(?:[\.,]\d{1,3})?", normalized)
    if not match:
        return None

    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None


def _normalize_purchase_date(value: Any, retailer: str) -> Optional[str]:
    if value is None:
        return None

    normalized = str(value).strip()
    if not normalized:
        return None

    if retailer == "rewe":
        iso_style = re.fullmatch(r"(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})", normalized)
        if iso_style:
            return normalized

        legacy_style = re.fullmatch(
            r"(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})(?:\s+\d{2}:\d{2}(?::\d{2})?)?",
            normalized,
        )
        if legacy_style:
            return (
                f"{legacy_style.group('year')}."
                f"{legacy_style.group('month')}."
                f"{legacy_style.group('day')}"
            )

    return normalized

