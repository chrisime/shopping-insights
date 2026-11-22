"""Store classified Rossmann coupon discounts."""

import sqlalchemy as sa
from alembic import op

revision = "0002_rossmann_coupons"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_rossmann",
        sa.Column("purchase_id", sa.Text(), primary_key=True),
        sa.Column("coupon_discount", sa.Float(), nullable=True),
        sa.Column("app_coupon_discount", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchase.id"], name="fk_purchase_rossmann__purchase", ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("purchase_rossmann")
