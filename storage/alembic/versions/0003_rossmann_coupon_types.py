"""Store the breakdown of Rossmann coupons by scope."""

import sqlalchemy as sa
from alembic import op

revision = "0003_rossmann_coupon_types"
down_revision = "0002_rossmann_coupons"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("purchase_rossmann", sa.Column("basket_coupon_discount", sa.Float()))
    op.add_column("purchase_rossmann", sa.Column("product_coupon_discount", sa.Float()))


def downgrade() -> None:
    op.drop_column("purchase_rossmann", "product_coupon_discount")
    op.drop_column("purchase_rossmann", "basket_coupon_discount")
