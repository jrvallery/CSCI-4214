"""create users table

Revision ID: 001
Revises:
Create Date: 2026-04-10
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("sport", sa.String(20), nullable=False),
        sa.Column("skill_level", sa.String(20), nullable=False),
        sa.Column("preferred_equipment", sa.String(20), nullable=False),
        sa.Column("preferred_terrain", sa.String(20), nullable=False),
        sa.Column("skier_type", sa.Integer(), nullable=True),
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("boot_sole_length_mm", sa.Integer(), nullable=True),
        sa.Column("din", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )


def downgrade() -> None:
    op.drop_table("users")
