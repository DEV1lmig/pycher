"""add_last_accessed_exercise_id_to_user_lesson_progress

Revision ID: 45ccc403761d
Revises: 5d8b23417d0d
Create Date: 2025-07-05 14:51:12.345678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '45ccc403761d'
down_revision: Union[str, None] = '5d8b23417d0d'
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
    table_name = 'user_lesson_progress'
    column_name = 'last_accessed_exercise_id'
    fk_name = 'fk_user_lesson_progress_last_accessed_exercise_id'

    if not column_exists(bind, table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=True))

    if not constraint_exists(bind, fk_name):
        # Clean up any orphaned exercise IDs before creating the foreign key
        op.execute(f"""
            UPDATE {table_name} ulp
            SET {column_name} = NULL
            WHERE NOT EXISTS (SELECT 1 FROM exercises e WHERE e.id = ulp.{column_name})
        """)
        op.create_foreign_key(
            fk_name,
            table_name, 'exercises',
            [column_name], ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    try:
        op.drop_constraint('fk_user_lesson_progress_last_accessed_exercise_id', 'user_lesson_progress', type_='foreignkey')
    except Exception:
        # Constraint might not exist
        pass
    if column_exists(bind, 'user_lesson_progress', 'last_accessed_exercise_id'):
        op.drop_column('user_lesson_progress', 'last_accessed_exercise_id')
