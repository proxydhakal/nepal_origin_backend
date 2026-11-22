"""Guest inquiry orders, quantity units, order replies, site map fields

Revision ID: c1d2e3f4a5b6
Revises: a9b8c7d6e5f4
Create Date: 2026-11-22 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "a9b8c7d6e5f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("order", "user_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("order", sa.Column("customer_name", sa.String(255), nullable=True))
    op.add_column("order", sa.Column("customer_email", sa.String(255), nullable=True))
    op.add_column("order", sa.Column("customer_phone", sa.String(50), nullable=True))
    op.add_column("order", sa.Column("customer_country", sa.String(100), nullable=True))
    op.add_column("order", sa.Column("customer_notes", sa.Text(), nullable=True))
    op.add_column("order", sa.Column("admin_notes", sa.Text(), nullable=True))

    op.alter_column(
        "orderitem",
        "quantity",
        existing_type=sa.Integer(),
        type_=sa.Numeric(12, 3),
        existing_nullable=False,
    )
    op.add_column(
        "orderitem",
        sa.Column("quantity_unit", sa.String(20), nullable=False, server_default="kg"),
    )

    op.create_table(
        "orderreply",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("order.id"), nullable=False, index=True),
        sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_to_email", sa.String(255), nullable=True),
    )

    op.add_column("siteconfig", sa.Column("map_embed_url", sa.Text(), nullable=True))
    op.add_column("siteconfig", sa.Column("map_latitude", sa.String(50), nullable=True))
    op.add_column("siteconfig", sa.Column("map_longitude", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("siteconfig", "map_longitude")
    op.drop_column("siteconfig", "map_latitude")
    op.drop_column("siteconfig", "map_embed_url")
    op.drop_table("orderreply")
    op.drop_column("orderitem", "quantity_unit")
    op.alter_column(
        "orderitem",
        "quantity",
        existing_type=sa.Numeric(12, 3),
        type_=sa.Integer(),
        existing_nullable=False,
    )
    op.drop_column("order", "admin_notes")
    op.drop_column("order", "customer_notes")
    op.drop_column("order", "customer_country")
    op.drop_column("order", "customer_phone")
    op.drop_column("order", "customer_email")
    op.drop_column("order", "customer_name")
    op.alter_column("order", "user_id", existing_type=sa.Integer(), nullable=False)
