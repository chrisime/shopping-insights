"""Shared schema helpers for normalized receipt dictionaries."""

from typing import Any, Dict, List, Optional

from shared.receipt_schema import normalize_receipt_schema


DEFAULT_RECEIPT_FIELDS = {
    "total_price": None,
    "total_price_no_saving": None,
    "saved_amount": None,
    "sticker_discount_amount": None,
    "sticker_discount_pct": [],
    "saved_pfand": None,
    "lidlplus_saved_amount": None,
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
        "purchase_date": purchase_date,
        "store": store,
    }

    for key, value in DEFAULT_RECEIPT_FIELDS.items():
        if isinstance(value, list):
            receipt_data[key] = list(value)
        else:
            receipt_data[key] = value

    receipt_data.update(overrides)
    return receipt_data



def build_receipt_item(
    name: str,
    price: str,
    quantity: str = "1",
    unit: str = "stk",
) -> Dict[str, str]:
    """Create a normalized receipt item dict."""
    return {
        "name": name,
        "price": price,
        "quantity": quantity,
        "unit": unit,
    }
