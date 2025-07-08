"""add explenation to exercises

Revision ID: 873420e24150
Revises: aebe0fd503a5
Create Date: 2025-06-22 01:29:43.089006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '873420e24150'
down_revision: Union[str, None] = 'aebe0fd503a5'
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

def constraint_exists(conn, constraint_name: str, schema: str = 'public') -> bool:
    """Checks if a constraint exists."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = :schema AND constraint_name = :constraint_name
        )
    """)
    return conn.execute(sql, {'schema': schema, 'constraint_name': constraint_name}).scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if not column_exists(bind, 'exercises', 'explanation'):
        op.add_column('exercises', sa.Column('explanation', sa.Text(), nullable=True))

    constraint_name = 'uq_user_lesson_progress'
    if constraint_exists(bind, constraint_name):
        op.drop_constraint(constraint_name, 'user_lesson_progress', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    constraint_name = 'uq_user_lesson_progress'
    if not constraint_exists(bind, constraint_name):
        op.create_unique_constraint(constraint_name, 'user_lesson_progress', ['user_id', 'lesson_id'])

    if column_exists(bind, 'exercises', 'explanation'):
        op.drop_column('exercises', 'explanation')
