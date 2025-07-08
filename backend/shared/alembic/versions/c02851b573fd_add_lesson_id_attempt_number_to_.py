"""add_lesson_id_attempt_number_to_submission_and_lesson_submissions_rel

Revision ID: c02851b573fd
Revises: 6537569d184a
Create Date: 2025-05-28 16:26:00.023772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c02851b573fd'
down_revision: Union[str, None] = '6537569d184a'
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

    if not column_exists(bind, table_name, 'lesson_id'):
        op.add_column(table_name, sa.Column('lesson_id', sa.Integer(), nullable=True))

    if not column_exists(bind, table_name, 'attempt_number'):
        op.add_column(table_name, sa.Column('attempt_number', sa.Integer(), nullable=True))

    op.execute('UPDATE user_exercise_submissions SET attempt_number = 1 WHERE attempt_number IS NULL')
    op.alter_column(table_name, 'attempt_number',
               existing_type=sa.INTEGER(),
               nullable=False,
               server_default=sa.text('1'))

    # IMPORTANT: This next line will fail if any rows have a NULL lesson_id.
    # You may need to add an `op.execute()` command before this to populate existing NULLs.
    op.alter_column(table_name, 'lesson_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    fk_name = 'fk_user_exercise_submissions_lesson_id_lessons'
    if not constraint_exists(bind, fk_name):
        op.create_foreign_key(fk_name, table_name, 'lessons', ['lesson_id'], ['id'])

    index_name = op.f('ix_user_exercise_submissions_lesson_id')
    if not index_exists(bind, index_name):
        op.create_index(index_name, table_name, ['lesson_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'user_exercise_submissions'
    index_name = op.f('ix_user_exercise_submissions_lesson_id')
    fk_name = 'fk_user_exercise_submissions_lesson_id_lessons'

    if index_exists(bind, index_name):
        op.drop_index(index_name, table_name=table_name)

    if constraint_exists(bind, fk_name):
        op.drop_constraint(fk_name, table_name, type_='foreignkey')

    if column_exists(bind, table_name, 'lesson_id'):
        op.drop_column(table_name, 'lesson_id')

    if column_exists(bind, table_name, 'attempt_number'):
        op.drop_column(table_name, 'attempt_number')
