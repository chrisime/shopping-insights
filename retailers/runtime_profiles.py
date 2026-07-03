"""Runtime-Profile für Retailer, abgeleitet aus dem Config-Modul."""

from __future__ import annotations

from dataclasses import dataclass

from config import LidlConfig, ReweConfig


@dataclass(frozen=True)
class RetailerRuntimeProfile:
    """Runtime-Daten eines Retailers, die aus der Konfiguration abgeleitet werden."""

    code: str
    name: str
    country: str
    receipts_json_file: str



def get_retailer_runtime_profile(retailer: str | None) -> RetailerRuntimeProfile | None:
    normalized_retailer = str(retailer or "").strip().lower()
    if not normalized_retailer:
        return None
    if normalized_retailer == "lidl":
        return RetailerRuntimeProfile(
            code="lidl",
            name="LIDL",
            country=LidlConfig.get_country_code(),
            receipts_json_file=LidlConfig.RECEIPTS_JSON_FILE,
        )
    if normalized_retailer == "rewe":
        return RetailerRuntimeProfile(
            code="rewe",
            name="REWE",
            country=ReweConfig.get_country_code(),
            receipts_json_file=ReweConfig.RECEIPTS_JSON_FILE,
        )
    return RetailerRuntimeProfile(
        code=normalized_retailer,
        name=normalized_retailer.upper(),
        country="",
        receipts_json_file="lidl_receipts.json",
    )

