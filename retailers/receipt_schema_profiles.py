"""Retailer-spezifische Receipt-Schema-Profile außerhalb von shared/config/storage."""

from __future__ import annotations

from shared.receipt_schema import ReceiptSchemaProfile


RETAILER_RECEIPT_SCHEMA_PROFILES: dict[str, ReceiptSchemaProfile] = {
    "lidl": ReceiptSchemaProfile(
        extra_defaults={
            "sticker_discount_amount": None,
            "sticker_discount_pct": [],
            "lidlplus_amount_saved": None,
        },
        extra_money_fields={
            "sticker_discount_amount",
            "lidlplus_amount_saved",
        },
    ),
    "rewe": ReceiptSchemaProfile(
        extra_defaults={
            "rewe_bonus_amount": None,
            "rewe_bonus_amount_saved": None,
            "rewe_bonus_total_amount": None,
        },
        extra_money_fields={
            "rewe_bonus_amount",
            "rewe_bonus_amount_saved",
            "rewe_bonus_total_amount",
        },
    ),
}



def get_receipt_schema_profile(retailer: str | None) -> ReceiptSchemaProfile:
    normalized_retailer = str(retailer or "").strip().lower()
    return RETAILER_RECEIPT_SCHEMA_PROFILES.get(normalized_retailer, ReceiptSchemaProfile())

