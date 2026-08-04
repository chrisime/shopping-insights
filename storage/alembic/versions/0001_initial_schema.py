"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-04

Mirrors the legacy V001__core_schema.sql layout. The hand-written cascade
triggers from the legacy schema are intentionally omitted; ``PRAGMA
foreign_keys = ON`` is enforced on every connection by ``storage.database``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retailer",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "store",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("retailer_code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("market", sa.Text(), nullable=True),
        sa.Column("street", sa.Text(), nullable=False),
        sa.Column("street_no", sa.Text(), nullable=False),
        sa.Column("zip", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("hash", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["retailer_code"], ["retailer.code"], name="fk_store__retailer", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash", name="uq_store__retailer_hash"),
    )
    op.create_index("idx_store__retailer_code", "store", ["retailer_code"], unique=False)
    op.create_table(
        "purchase",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("purchase_date", sa.Text(), nullable=False),
        sa.Column("bon_number", sa.Text(), nullable=True),
        sa.Column("register_id", sa.Text(), nullable=True),
        sa.Column("cashier", sa.Text(), nullable=True),
        sa.Column("total_price", sa.Float(), nullable=True),
        sa.Column("discount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("saved_deposit", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.Text(), nullable=False, server_default="EUR"),
        sa.Column("source_file", sa.Text(), nullable=True),
        sa.Column("hash", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["store.id"], name="fk_purchase__store", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hash", name="uq_purchase__hash"),
    )
    op.create_index("idx_purchase__store_id", "purchase", ["store_id"], unique=False)
    op.create_table(
        "purchase_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchase_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit", sa.Text(), nullable=False, server_default="stk"),
        sa.Column("price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchase.id"], name="fk_purchase_item__purchase", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchase_id", "position", name="uq_purchase_item__purchase_position"),
    )
    op.create_table(
        "payment_method",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchase_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("method", sa.Text(), nullable=False),
        sa.Column("network", sa.Text(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchase.id"], name="fk_payment_method__purchase", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("purchase_id", "position", name="uq_payment_method__purchase_position"),
    )
    op.create_table(
        "purchase_lidl",
        sa.Column("purchase_id", sa.Text(), nullable=False),
        sa.Column("lidlplus_discount", sa.Float(), nullable=True),
        sa.Column("sticker_discount", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchase.id"], name="fk_purchase_lidl__purchase", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("purchase_id"),
    )
    op.create_table(
        "purchase_rewe",
        sa.Column("purchase_id", sa.Text(), nullable=False),
        sa.Column("rewe_bonus_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rewe_bonus_total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rewe_bonus_discount", sa.Float(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchase.id"], name="fk_purchase_rewe__purchase", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("purchase_id"),
    )


def downgrade() -> None:
    op.drop_table("purchase_rewe")
    op.drop_table("purchase_lidl")
    op.drop_table("payment_method")
    op.drop_table("purchase_item")
    op.drop_index("idx_purchase__store_id", table_name="purchase")
    op.drop_table("purchase")
    op.drop_index("idx_store__retailer_code", table_name="store")
    op.drop_table("store")
    op.drop_table("retailer")
