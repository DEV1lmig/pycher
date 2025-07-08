"""added is_active status to Lesson and Module

Revision ID: a6b4a3078af1
Revises: 2ae7dcb6b687
Create Date: 2025-06-03 10:41:10.411517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a6b4a3078af1'
down_revision: Union[str, None] = '2ae7dcb6b687'
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

    if not column_exists(bind, 'lessons', 'is_active'):
        op.add_column('lessons', sa.Column('is_active', sa.Boolean(), nullable=True))

    if not column_exists(bind, 'modules', 'is_active'):
        op.add_column('modules', sa.Column('is_active', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    if column_exists(bind, 'modules', 'is_active'):
        op.drop_column('modules', 'is_active')

    if column_exists(bind, 'lessons', 'is_active'):
        op.drop_column('lessons', 'is_active')
