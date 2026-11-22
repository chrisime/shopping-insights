"""Keep the coupon names and savings for Rossmann receipt details."""

import sqlalchemy as sa
from alembic import op

revision = "0004_rossmann_coupon_details"
down_revision = "0003_rossmann_coupon_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("purchase_rossmann", sa.Column("coupons", sa.JSON(none_as_null=True)))


def downgrade() -> None:
    op.drop_column("purchase_rossmann", "coupons")
