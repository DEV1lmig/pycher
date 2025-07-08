"""add_difficulty

Revision ID: b3da0acefc5c
Revises: cf36296cfcaa
Create Date: 2025-06-02 19:43:23.568714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'b3da0acefc5c'
down_revision: Union[str, None] = 'cf36296cfcaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, table_name: str, column_name: str, schema: str = 'public') -> bool:
    """Checks if a column exists in a table."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table_name AND column_name = :column_name
        )
    """)
    return conn.execute(sql, {'schema': schema, 'table_name': table_name, 'column_name': column_name}).scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    table_name = 'exercises'
    column_name = 'difficulty'
    if not column_exists(bind, table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'exercises'
    column_name = 'difficulty'
    if column_exists(bind, table_name, column_name):
        op.drop_column(table_name, column_name)
