"""added course id to execerices

Revision ID: 44a5ef4c3573
Revises: d0887f6625a7
Create Date: 2025-06-06 12:29:42.082752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '44a5ef4c3573'
down_revision: Union[str, None] = 'd0887f6625a7'
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
    table_name = 'exercises'
    column_name = 'course_id'
    fk_name = 'fk_exercises_course_id_courses'

    if not column_exists(bind, table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=True))

    if not constraint_exists(bind, fk_name):
        op.create_foreign_key(fk_name, table_name, 'courses', [column_name], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'exercises'
    column_name = 'course_id'
    fk_name = 'fk_exercises_course_id_courses'

    if constraint_exists(bind, fk_name):
        op.drop_constraint(fk_name, table_name, type_='foreignkey')

    if column_exists(bind, table_name, column_name):
        op.drop_column(table_name, column_name)
