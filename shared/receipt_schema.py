"""Neutrale Schema-Helfer für normalisierte Receipt-Dictionaries."""

import re
from typing import Any, Dict, List, Optional

from config.receipt_schema_profiles import ReceiptSchemaProfile

from shared.addresses import empty_address, normalize_address
from shared.receipt_dates import normalize_purchase_date
from shared.payment_methods import normalize_payment_method_entry


SHARED_MONEY_FIELDS = {
    "total_price",
    "amount_saved",
    "saved_deposit",
}


SHARED_RECEIPT_FIELDS = {
    "total_price": None,
    "amount_saved": None,
    "saved_deposit": None,
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
    profile: Optional[ReceiptSchemaProfile] = None,
    **overrides: Any,
) -> Dict[str, Any]:
    """Create a normalized receipt dict with shared core and optional fields."""
    receipt_data = {
        "id": receipt_id,
        "retailer": retailer,
        "purchase_date": _normalize_optional_text(purchase_date),
        "store": store,
    }

    for key, value in SHARED_RECEIPT_FIELDS.items():
        receipt_data[key] = _copy_default_value(value)

    if profile:
        for key, value in profile.extra_defaults.items():
            receipt_data[key] = _copy_default_value(value)

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
    profile: Optional[ReceiptSchemaProfile] = None,
) -> Dict[str, Any]:
    """Merge an existing receipt dict into the shared schema defaults."""
    resolved_retailer = _resolve_receipt_retailer(receipt_data, retailer)
    normalized = _build_normalized_receipt_base(receipt_data, resolved_retailer, profile)
    normalized.update(receipt_data)
    _normalize_receipt_metadata_fields(normalized, resolved_retailer)
    _restore_mutable_defaults(normalized, profile)
    _normalize_receipt_address(normalized)
    _normalize_receipt_money_fields(normalized, profile)
    _normalize_receipt_collection_fields(normalized)
    return normalized


def _normalize_optional_text(value: str | None) -> Optional[str]:
    if value is None:
        return None
    return value.strip() or None


def _resolve_receipt_retailer(
    receipt_data: Dict[str, Any],
    retailer: Optional[str] = None,
) -> str:
    resolved_retailer = _normalize_optional_text(retailer or receipt_data.get("retailer"))
    if resolved_retailer is None:
        raise ValueError("Receipt retailer fehlt für die Schema-Normalisierung")
    return resolved_retailer


def _build_normalized_receipt_base(
    receipt_data: Dict[str, Any],
    retailer: str,
    profile: Optional[ReceiptSchemaProfile] = None,
) -> Dict[str, Any]:
    return build_receipt_schema(
        receipt_id=receipt_data.get("id") or receipt_data.get("url") or "",
        retailer=retailer,
        purchase_date=receipt_data.get("purchase_date"),
        store=receipt_data.get("store"),
        profile=profile,
    )


def _normalize_receipt_metadata_fields(normalized: Dict[str, Any], retailer: str) -> None:
    normalized["retailer"] = retailer
    normalized["purchase_date"] = normalize_purchase_date(normalized.get("purchase_date"))
    normalized.pop("total_price_no_saving", None)


def _restore_mutable_defaults(normalized: Dict[str, Any], profile: Optional[ReceiptSchemaProfile] = None) -> None:
    for field_name, default_value in SHARED_RECEIPT_FIELDS.items():
        if normalized.get(field_name) is None:
            normalized[field_name] = _copy_default_value(default_value)

    if profile:
        for field_name, default_value in profile.extra_defaults.items():
            if normalized.get(field_name) is None:
                normalized[field_name] = _copy_default_value(default_value)


def _copy_default_value(value: Any) -> Any:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def _normalize_receipt_address(normalized: Dict[str, Any]) -> None:
    normalized["address"] = normalize_address(normalized.get("address"))


def _normalize_receipt_money_fields(normalized: Dict[str, Any], profile: Optional[ReceiptSchemaProfile] = None) -> None:
    for field_name in SHARED_MONEY_FIELDS:
        if field_name in normalized:
            normalized[field_name] = _normalize_money_value(normalized.get(field_name))

    if profile:
        for field_name in profile.extra_money_fields:
            if field_name in normalized:
                normalized[field_name] = _normalize_money_value(normalized.get(field_name))


def _normalize_receipt_collection_fields(normalized: Dict[str, Any]) -> None:
    normalized["payment_methods"] = _normalize_payment_methods(
        normalized.get("payment_methods"),
        retailer=normalized.get("retailer"),
    )
    normalized["items"] = _normalize_items(normalized.get("items"))


def _normalize_payment_methods(payment_methods: Any, *, retailer: Any = None) -> List[Dict[str, Any]]:
    normalized_methods: List[Dict[str, Any]] = []
    for payment_method in payment_methods or []:
        if not isinstance(payment_method, dict):
            continue
        normalized_method = normalize_payment_method_entry(
            {
                **payment_method,
                "retailer": retailer,
            }
        )
        if normalized_method:
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
        normalized_item["quantity"] = _normalize_quantity_value(normalized_item.get("quantity"), normalized_item["unit"])
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

    match = re.search(r"-?\d+(?:[.,]\d{1,2})?", normalized)
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

    match = re.search(r"-?\d+(?:[.,]\d{1,3})?", normalized)
    if not match:
        return None

    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None
