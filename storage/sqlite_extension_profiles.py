"""Neutrale SQLite-Extension-Profile und Registry für retailer-spezifische Storage-Erweiterungen."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from shared.receipt_schema import ReceiptSchemaProfile


@dataclass(frozen=True)
class SqlitePurchaseExtensionProfile:
    """SQLite-spezifisches Profil für retailer-spezifische Purchase-Erweiterungen."""

    table_name: str
    create_table_sql: str
    insert_sql: str
    value_factory: Callable[[dict[str, Any]], tuple[Any, ...]]


@dataclass(frozen=True)
class RetailerPersistenceProfile:
    """Vendor-spezifische Persistenzmetadaten für einen Retailer."""

    code: str
    name: str
    country: str
    receipt_schema_profile: ReceiptSchemaProfile = field(default_factory=ReceiptSchemaProfile)
    sqlite_purchase_extension: SqlitePurchaseExtensionProfile | None = None


from .lidl_extension_store import get_lidl_persistence_profile
from .rewe_extension_store import get_rewe_persistence_profile


_REGISTERED_RETAILER_PERSISTENCE_PROFILES: dict[str, Callable[[], RetailerPersistenceProfile]] = {
    "lidl": get_lidl_persistence_profile,
    "rewe": get_rewe_persistence_profile,
}



def get_retailer_persistence_profile(retailer: str | None) -> RetailerPersistenceProfile | None:
    normalized_retailer = str(retailer or "").strip().lower()
    if not normalized_retailer:
        return None
    factory = _REGISTERED_RETAILER_PERSISTENCE_PROFILES.get(normalized_retailer)
    if factory is None:
        return RetailerPersistenceProfile(
            code=normalized_retailer,
            name=normalized_retailer.upper(),
            country="",
        )
    return factory()



def get_all_retailer_persistence_profiles() -> tuple[RetailerPersistenceProfile, ...]:
    return tuple(factory() for factory in _REGISTERED_RETAILER_PERSISTENCE_PROFILES.values())

