"""Modify Exercise table for dynamic validation: remove solution_code, test_cases; add validation_type, validation_rules

Revision ID: da6813d14813
Revises: f386dfb619d3
Create Date: 2025-05-29 14:50:47.697524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'da6813d14813'
down_revision: Union[str, None] = 'f386dfb619d3'
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

    if not column_exists(bind, table_name, 'validation_type'):
        op.add_column(table_name, sa.Column('validation_type', sa.String(), nullable=True))

    if not column_exists(bind, table_name, 'validation_rules'):
        op.add_column(table_name, sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    if column_exists(bind, table_name, 'solution_code'):
        op.drop_column(table_name, 'solution_code')

    if column_exists(bind, table_name, 'test_cases'):
        op.drop_column(table_name, 'test_cases')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'exercises'

    if not column_exists(bind, table_name, 'test_cases'):
        op.add_column(table_name, sa.Column('test_cases', sa.TEXT(), autoincrement=False, nullable=True))

    if not column_exists(bind, table_name, 'solution_code'):
        op.add_column(table_name, sa.Column('solution_code', sa.TEXT(), autoincrement=False, nullable=True))

    if column_exists(bind, table_name, 'validation_rules'):
        op.drop_column(table_name, 'validation_rules')

    if column_exists(bind, table_name, 'validation_type'):
        op.drop_column(table_name, 'validation_type')
