"""add_user_progress_id_to_user_exercise_submissions

Revision ID: f386dfb619d3
Revises: c02851b573fd
Create Date: 2025-05-28 18:27:28.630836

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f386dfb619d3'
down_revision: Union[str, None] = 'c02851b573fd'
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

def index_exists(conn, index_name: str, schema: str = 'public') -> bool:
    """Checks if an index exists."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'i' AND n.nspname = :schema AND c.relname = :index_name
        )
    """)
    return conn.execute(sql, {'schema': schema, 'index_name': index_name}).scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    table_name = 'user_exercise_submissions'

    if not column_exists(bind, table_name, 'user_progress_id'):
        op.add_column(table_name, sa.Column('user_progress_id', sa.Integer(), nullable=True))

    if column_exists(bind, table_name, 'is_correct'):
        op.execute(f"UPDATE {table_name} SET is_correct = false WHERE is_correct IS NULL")
        op.alter_column(table_name, 'is_correct',
                   existing_type=sa.BOOLEAN(),
                   nullable=False)

    if column_exists(bind, table_name, 'submitted_at'):
        op.alter_column(table_name, 'submitted_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   type_=sa.DateTime(),
                   existing_nullable=True,
                   existing_server_default=sa.text('now()'))

    index_to_drop = 'ix_user_exercise_submissions_lesson_id'
    if index_exists(bind, index_to_drop):
        op.drop_index(index_to_drop, table_name=table_name)

    fk_progress_name = 'fk_user_exercise_submissions_user_progress_id'
    if not constraint_exists(bind, fk_progress_name):
        op.create_foreign_key(fk_progress_name, table_name, 'user_progress', ['user_progress_id'], ['id'])

    fk_user_name = 'fk_user_exercise_submissions_user_id'
    if not constraint_exists(bind, fk_user_name):
        op.create_foreign_key(fk_user_name, table_name, 'users', ['user_id'], ['id'])

    if column_exists(bind, table_name, 'attempts'):
        op.drop_column(table_name, 'attempts')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'user_exercise_submissions'

    if not column_exists(bind, table_name, 'attempts'):
        op.add_column(table_name, sa.Column('attempts', sa.INTEGER(), autoincrement=False, nullable=True))

    fk_progress_name = 'fk_user_exercise_submissions_user_progress_id'
    if constraint_exists(bind, fk_progress_name):
        op.drop_constraint(fk_progress_name, table_name, type_='foreignkey')

    fk_user_name = 'fk_user_exercise_submissions_user_id'
    if constraint_exists(bind, fk_user_name):
        op.drop_constraint(fk_user_name, table_name, type_='foreignkey')

    index_to_create = 'ix_user_exercise_submissions_lesson_id'
    if not index_exists(bind, index_to_create):
        op.create_index(index_to_create, table_name, ['lesson_id'], unique=False)

    if column_exists(bind, table_name, 'submitted_at'):
        op.alter_column(table_name, 'submitted_at',
                   existing_type=sa.DateTime(),
                   type_=postgresql.TIMESTAMP(timezone=True),
                   existing_nullable=True,
                   existing_server_default=sa.text('now()'))

    if column_exists(bind, table_name, 'is_correct'):
        op.alter_column(table_name, 'is_correct',
                   existing_type=sa.BOOLEAN(),
                   nullable=True)

    if column_exists(bind, table_name, 'user_progress_id'):
        op.drop_column(table_name, 'user_progress_id')
