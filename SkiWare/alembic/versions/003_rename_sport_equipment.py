"""rename sport→preferred_sport and preferred_equipment→equipment (JSON list)

Revision ID: 003
Revises: 002
Create Date: 2026-04-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "sport", new_column_name="preferred_sport")
    op.alter_column(
        "users",
        "preferred_equipment",
        new_column_name="equipment",
        type_=sa.JSON,
        postgresql_using="json_build_array(preferred_equipment)",
        existing_type=sa.String(20),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "equipment",
        new_column_name="preferred_equipment",
        type_=sa.String(20),
        postgresql_using="equipment->>0",
        existing_type=sa.JSON,
        existing_nullable=False,
    )
    op.alter_column("users", "preferred_sport", new_column_name="sport")
