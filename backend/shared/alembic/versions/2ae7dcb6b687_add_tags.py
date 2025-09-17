"""add_tags

Revision ID: 2ae7dcb6b687
Revises: 2a04fdeff7cd
Create Date: 2025-06-02 19:45:48.104819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '2ae7dcb6b687'
down_revision: Union[str, None] = '2a04fdeff7cd'
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
    column_name = 'tags'
    if not column_exists(bind, table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'exercises'
    column_name = 'tags'
    if column_exists(bind, table_name, column_name):
        op.drop_column(table_name, column_name)
