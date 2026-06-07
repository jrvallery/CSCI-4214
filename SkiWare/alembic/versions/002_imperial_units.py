"""switch weight and height to imperial units

Revision ID: 002
Revises: 001
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "weight_kg", new_column_name="weight_lbs")
    op.alter_column("users", "height_cm", new_column_name="height_in")


def downgrade() -> None:
    op.alter_column("users", "weight_lbs", new_column_name="weight_kg")
    op.alter_column("users", "height_in", new_column_name="height_cm")
