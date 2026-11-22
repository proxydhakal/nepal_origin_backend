"""newsletter unsubscribe token and is_active

Revision ID: g4h5i6j7k8l9
Revises: e3f4a5b6c7d8
Create Date: 2026-11-22 13:30:00.000000

"""
from typing import Sequence, Union
import secrets

from alembic import op
import sqlalchemy as sa


revision: str = "g4h5i6j7k8l9"
down_revision: Union[str, None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure table exists (older DBs may have skipped orphaned migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "newsletter_subscriber" not in tables:
        op.create_table(
            "newsletter_subscriber",
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("unsubscribe_token", sa.String(length=64), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_newsletter_subscriber_email"), "newsletter_subscriber", ["email"], unique=True)
        op.create_index(
            op.f("ix_newsletter_subscriber_unsubscribe_token"),
            "newsletter_subscriber",
            ["unsubscribe_token"],
            unique=True,
        )
        return

    columns = {c["name"] for c in inspector.get_columns("newsletter_subscriber")}
    if "is_active" not in columns:
        op.add_column(
            "newsletter_subscriber",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        )
    if "unsubscribe_token" not in columns:
        op.add_column(
            "newsletter_subscriber",
            sa.Column("unsubscribe_token", sa.String(length=64), nullable=True),
        )
        # Backfill tokens for existing rows
        rows = conn.execute(sa.text("SELECT id FROM newsletter_subscriber")).fetchall()
        for (row_id,) in rows:
            token = secrets.token_urlsafe(24)
            conn.execute(
                sa.text("UPDATE newsletter_subscriber SET unsubscribe_token = :t WHERE id = :id"),
                {"t": token, "id": row_id},
            )
        op.alter_column(
            "newsletter_subscriber",
            "unsubscribe_token",
            existing_type=sa.String(length=64),
            nullable=False,
        )
        op.create_index(
            op.f("ix_newsletter_subscriber_unsubscribe_token"),
            "newsletter_subscriber",
            ["unsubscribe_token"],
            unique=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "newsletter_subscriber" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("newsletter_subscriber")}
    indexes = {i["name"] for i in inspector.get_indexes("newsletter_subscriber")}
    if "ix_newsletter_subscriber_unsubscribe_token" in indexes:
        op.drop_index(op.f("ix_newsletter_subscriber_unsubscribe_token"), table_name="newsletter_subscriber")
    if "unsubscribe_token" in columns:
        op.drop_column("newsletter_subscriber", "unsubscribe_token")
    if "is_active" in columns:
        op.drop_column("newsletter_subscriber", "is_active")
