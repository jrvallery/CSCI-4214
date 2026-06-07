"""create assessments table

Revision ID: 005
Revises: 004
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            equipment_type VARCHAR(20) NOT NULL,
            brand VARCHAR NOT NULL DEFAULT '',
            safe_to_ski BOOLEAN NOT NULL,
            severity INTEGER NOT NULL,
            verdict VARCHAR(10) NOT NULL,
            request_data JSON NOT NULL,
            response_data JSON NOT NULL,
            created_at TIMESTAMPTZ NOT NULL
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_assessments_user_id ON assessments (user_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_assessments_user_id")
    op.execute("DROP TABLE IF EXISTS assessments")
