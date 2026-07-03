"""LIDL-spezifische SQLite-Extension-Profile für den Storage-Layer."""

from __future__ import annotations

from config import LidlConfig, get_receipt_schema_profile

from .sqlite_extension_profiles import (
    RetailerPersistenceProfile,
    SqlitePurchaseExtensionProfile,
)



def _build_lidl_sqlite_extension_values(receipt_data: dict[str, object]) -> tuple[object, ...]:
    purchase_id = str(receipt_data["id"])
    return (
        purchase_id,
        receipt_data.get("lidlplus_amount_saved"),
        receipt_data.get("sticker_discount_amount"),
    )



def get_lidl_persistence_profile() -> RetailerPersistenceProfile:
    return RetailerPersistenceProfile(
        code="lidl",
        name="LIDL",
        country=LidlConfig.get_country_code(),
        receipt_schema_profile=get_receipt_schema_profile("lidl"),
        sqlite_purchase_extension=SqlitePurchaseExtensionProfile(
            table_name="purchase_lidl",
            create_table_sql="""
create table if not exists purchase_lidl (
    purchase_id text primary key,
    lidlplus_amount_saved real,
    sticker_discount_amount real,

    constraint fk_purchase_lidl__purchase
        foreign key (purchase_id) references purchase(id) on delete cascade
);
""".strip(),
            insert_sql="""
insert into purchase_lidl (
    purchase_id,
    lidlplus_amount_saved,
    sticker_discount_amount
)
values (?, ?, ?)
""".strip(),
            value_factory=_build_lidl_sqlite_extension_values,
        ),
    )

