"""Receipt-Schema-Profile für unterstützte Händler."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReceiptSchemaProfile:
    """Konkretes Händlerprofil für zusätzliche Receipt-Felder außerhalb von shared."""

    extra_defaults: dict[str, object] = field(default_factory=dict)
    extra_money_fields: set[str] = field(default_factory=set)

_SCHEMA_PROFILES = {
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
    retailer_code = str(retailer or "").strip().lower()
    if not retailer_code:
        return ReceiptSchemaProfile()
    return _SCHEMA_PROFILES.get(retailer_code, ReceiptSchemaProfile())

