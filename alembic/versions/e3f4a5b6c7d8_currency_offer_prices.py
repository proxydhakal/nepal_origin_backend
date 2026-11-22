"""Add USD/NPR pricing and offer prices on variants

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-11-22 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("productvariant", sa.Column("price_usd", sa.Numeric(10, 2), nullable=True))
    op.add_column("productvariant", sa.Column("offer_price", sa.Numeric(10, 2), nullable=True))
    op.add_column("productvariant", sa.Column("offer_price_usd", sa.Numeric(10, 2), nullable=True))
    op.add_column(
        "productvariant",
        sa.Column("currency", sa.String(10), nullable=False, server_default="NPR"),
    )


def downgrade() -> None:
    op.drop_column("productvariant", "currency")
    op.drop_column("productvariant", "offer_price_usd")
    op.drop_column("productvariant", "offer_price")
    op.drop_column("productvariant", "price_usd")
