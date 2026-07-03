"""Kompakte Händler-Profile für Schema-Defaults und runtime-nahe Receipt-Ziele."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.receipt_schema import ReceiptSchemaProfile

from .lidl_config import LidlConfig
from .rewe_config import ReweConfig


LIDL_RECEIPT_SCHEMA_PROFILE = ReceiptSchemaProfile(
    extra_defaults={
        "sticker_discount_amount": None,
        "sticker_discount_pct": [],
        "lidlplus_amount_saved": None,
    },
    extra_money_fields={
        "sticker_discount_amount",
        "lidlplus_amount_saved",
    },
)

REWE_RECEIPT_SCHEMA_PROFILE = ReceiptSchemaProfile(
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
)


@dataclass(frozen=True)
class RetailerProfile:
    """Lesbares Gesamtprofil eines unterstützten Händlers."""

    code: str
    name: str
    country: str
    receipts_json_file: str
    receipt_schema_profile: ReceiptSchemaProfile = field(default_factory=ReceiptSchemaProfile)



def get_retailer_profile(retailer: str | None) -> RetailerProfile | None:
    normalized_retailer = str(retailer or "").strip().lower()
    if not normalized_retailer:
        return None
    if normalized_retailer == "lidl":
        return RetailerProfile(
            code="lidl",
            name="LIDL",
            country=LidlConfig.get_country_code(),
            receipts_json_file=LidlConfig.RECEIPTS_JSON_FILE,
            receipt_schema_profile=LIDL_RECEIPT_SCHEMA_PROFILE,
        )
    if normalized_retailer == "rewe":
        return RetailerProfile(
            code="rewe",
            name="REWE",
            country=ReweConfig.get_country_code(),
            receipts_json_file=ReweConfig.RECEIPTS_JSON_FILE,
            receipt_schema_profile=REWE_RECEIPT_SCHEMA_PROFILE,
        )
    return None



def get_receipt_schema_profile(retailer: str | None) -> ReceiptSchemaProfile:
    retailer_profile = get_retailer_profile(retailer)
    if retailer_profile is None:
        return ReceiptSchemaProfile()
    return retailer_profile.receipt_schema_profile



def resolve_retailer_receipts_json_file(
    retailer: str | None,
    file_path: str | None = None,
    default_retailer: str = "lidl",
) -> str:
    """Resolve the retailer-specific JSON receipts target directly from config-backed profiles."""
    if file_path:
        return file_path

    retailer_profile = get_retailer_profile(retailer or default_retailer)
    if retailer_profile is None:
        raise ValueError(f"Unbekannter Händler für Receipt-Storage: {retailer}")
    return retailer_profile.receipts_json_file

