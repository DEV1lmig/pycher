"""added order_index to course_exam

Revision ID: aebe0fd503a5
Revises: f26518a324a0
Create Date: 2025-06-22 01:28:16.142010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'aebe0fd503a5'
down_revision: Union[str, None] = 'f26518a324a0'
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
    if not column_exists(bind, 'course_exams', 'order_index'):
        op.add_column('course_exams', sa.Column('order_index', sa.Integer(), nullable=True))
        op.execute("UPDATE course_exams SET order_index = 0 WHERE order_index IS NULL")
        op.alter_column('course_exams', 'order_index', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    constraint_name = 'uq_user_lesson_progress'
    if not constraint_exists(bind, constraint_name):
        op.create_unique_constraint(constraint_name, 'user_lesson_progress', ['user_id', 'lesson_id'])

    if column_exists(bind, 'course_exams', 'order_index'):
        op.drop_column('course_exams', 'order_index')
