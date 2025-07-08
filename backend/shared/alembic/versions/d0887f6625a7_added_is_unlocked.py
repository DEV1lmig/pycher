"""added_is_unlocked

Revision ID: d0887f6625a7
Revises: 901030a37341
Create Date: 2025-06-04 16:58:57.419218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd0887f6625a7'
down_revision: Union[str, None] = '901030a37341'
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
    table_name = 'user_module_progress'
    column_name = 'is_unlocked'
    if not column_exists(bind, table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'user_module_progress'
    column_name = 'is_unlocked'
    if column_exists(bind, table_name, column_name):
        op.drop_column(table_name, column_name)
