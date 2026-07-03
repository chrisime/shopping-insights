"""REWE-spezifische SQLite-Extension-Profile für den Storage-Layer."""

from __future__ import annotations

from config import ReweConfig, get_receipt_schema_profile

from .sqlite_extension_profiles import (
    RetailerPersistenceProfile,
    SqlitePurchaseExtensionProfile,
)



def _build_rewe_sqlite_extension_values(receipt_data: dict[str, object]) -> tuple[object, ...]:
    purchase_id = str(receipt_data["id"])
    return (
        purchase_id,
        receipt_data.get("rewe_bonus_amount") or 0.0,
        receipt_data.get("rewe_bonus_total_amount") or 0.0,
        receipt_data.get("rewe_bonus_amount_saved") or 0.0,
    )



def get_rewe_persistence_profile() -> RetailerPersistenceProfile:
    return RetailerPersistenceProfile(
        code="rewe",
        name="REWE",
        country=ReweConfig.get_country_code(),
        receipt_schema_profile=get_receipt_schema_profile("rewe"),
        sqlite_purchase_extension=SqlitePurchaseExtensionProfile(
            table_name="purchase_rewe",
            create_table_sql="""
create table if not exists purchase_rewe (
    purchase_id text primary key,
    rewe_bonus_amount real not null default 0,
    rewe_bonus_total_amount real not null default 0,
    rewe_bonus_amount_saved real not null default 0,

    constraint fk_purchase_rewe__purchase
        foreign key (purchase_id) references purchase(id) on delete cascade
);
""".strip(),
            insert_sql="""
insert into purchase_rewe (
    purchase_id,
    rewe_bonus_amount,
    rewe_bonus_total_amount,
    rewe_bonus_amount_saved
)
values (?, ?, ?, ?)
""".strip(),
            value_factory=_build_rewe_sqlite_extension_values,
        ),
    )

