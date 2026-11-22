"""add purpose column to verification_otp for password_reset

Revision ID: a9b8c7d6e5f4
Revises: c4d5e6f7a8b9
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "verification_otp",
        sa.Column("purpose", sa.String(32), nullable=True, server_default="email_verification"),
    )
    op.alter_column(
        "verification_otp",
        "purpose",
        existing_type=sa.String(32),
        nullable=False,
        server_default="email_verification",
    )
    op.create_index(op.f("ix_verification_otp_purpose"), "verification_otp", ["purpose"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_otp_purpose"), table_name="verification_otp")
    op.drop_column("verification_otp", "purpose")
