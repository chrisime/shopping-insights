"""Retailer-Metadatenprofile für Persistenzadapter außerhalb von storage/shared."""

from __future__ import annotations

from dataclasses import dataclass

from .lidl_config import LidlConfig
from .rewe_config import ReweConfig


@dataclass(frozen=True)
class RetailerPersistenceProfile:
    """Vendor-spezifische Persistenzmetadaten für einen Retailer."""

    code: str
    name: str
    country: str



def get_retailer_persistence_profile(retailer: str | None) -> RetailerPersistenceProfile | None:
    normalized_retailer = str(retailer or "").strip().lower()
    if not normalized_retailer:
        return None
    if normalized_retailer == "lidl":
        return RetailerPersistenceProfile(
            code="lidl",
            name="LIDL",
            country=LidlConfig.get_country_code(),
        )
    if normalized_retailer == "rewe":
        return RetailerPersistenceProfile(
            code="rewe",
            name="REWE",
            country=ReweConfig.get_country_code(),
        )
    return RetailerPersistenceProfile(
        code=normalized_retailer,
        name=normalized_retailer.upper(),
        country="",
    )

