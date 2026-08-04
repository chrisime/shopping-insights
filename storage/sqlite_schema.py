"""SQLAlchemy Core table definitions for the SQLite receipt database.

Single source of truth for the schema. Alembic autogenerate compares against
this metadata; the domains and stores reference these tables.
"""

from __future__ import annotations

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, MetaData, Table, Text, UniqueConstraint

metadata = MetaData()

retailer_table = Table(
    "retailer",
    metadata,
    Column("code", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("country", Text, nullable=False),
)

store_table = Table(
    "store",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("retailer_code", Text, ForeignKey("retailer.code", ondelete="CASCADE", name="fk_store__retailer"), nullable=False),
    Column("name", Text, nullable=False),
    Column("market", Text, nullable=True),
    Column("street", Text, nullable=False),
    Column("street_no", Text, nullable=False),
    Column("zip", Text, nullable=False),
    Column("city", Text, nullable=False),
    Column("hash", Text, nullable=False),
    UniqueConstraint("hash", name="uq_store__retailer_hash"),
)

Index("idx_store__retailer_code", store_table.c.retailer_code)

purchase_table = Table(
    "purchase",
    metadata,
    Column("id", Text, primary_key=True),
    Column("store_id", Integer, ForeignKey("store.id", ondelete="CASCADE", name="fk_purchase__store"), nullable=True),
    Column("purchase_date", Text, nullable=False),
    Column("bon_number", Text, nullable=True),
    Column("register_id", Text, nullable=True),
    Column("cashier", Text, nullable=True),
    Column("total_price", Float, nullable=True),
    Column("discount", Float, nullable=False, server_default="0"),
    Column("saved_deposit", Float, nullable=False, server_default="0"),
    Column("currency", Text, nullable=False, server_default="EUR"),
    Column("source_file", Text, nullable=True),
    Column("hash", Text, nullable=False),
    UniqueConstraint("hash", name="uq_purchase__hash"),
)

Index("idx_purchase__store_id", purchase_table.c.store_id)

purchase_item_table = Table(
    "purchase_item",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("purchase_id", Text, ForeignKey("purchase.id", ondelete="CASCADE", name="fk_purchase_item__purchase"), nullable=False),
    Column("position", Integer, nullable=False),
    Column("name", Text, nullable=False),
    Column("quantity", Float, nullable=False, server_default="1"),
    Column("unit", Text, nullable=False, server_default="stk"),
    Column("price", Float, nullable=False),
    UniqueConstraint("purchase_id", "position", name="uq_purchase_item__purchase_position"),
)

payment_method_table = Table(
    "payment_method",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("purchase_id", Text, ForeignKey("purchase.id", ondelete="CASCADE", name="fk_payment_method__purchase"), nullable=False),
    Column("position", Integer, nullable=False),
    Column("method", Text, nullable=False),
    Column("network", Text, nullable=True),
    Column("amount", Float, nullable=True),
    UniqueConstraint("purchase_id", "position", name="uq_payment_method__purchase_position"),
)

purchase_lidl_table = Table(
    "purchase_lidl",
    metadata,
    Column("purchase_id", Text, ForeignKey("purchase.id", ondelete="CASCADE", name="fk_purchase_lidl__purchase"), primary_key=True),
    Column("lidlplus_discount", Float, nullable=True),
    Column("sticker_discount", Float, nullable=True),
)

purchase_rewe_table = Table(
    "purchase_rewe",
    metadata,
    Column("purchase_id", Text, ForeignKey("purchase.id", ondelete="CASCADE", name="fk_purchase_rewe__purchase"), primary_key=True),
    Column("rewe_bonus_amount", Float, nullable=False, server_default="0"),
    Column("rewe_bonus_total_amount", Float, nullable=False, server_default="0"),
    Column("rewe_bonus_discount", Float, nullable=False, server_default="0"),
)
