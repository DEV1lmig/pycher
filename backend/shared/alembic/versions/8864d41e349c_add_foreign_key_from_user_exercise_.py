"""Add foreign key from user_exercise_submissions to users for user relationship

Revision ID: 8864d41e349c
Revises: da6813d14813
Create Date: 2025-05-29 15:23:01.614656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '8864d41e349c'
down_revision: Union[str, None] = 'da6813d14813'
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
    submissions_table = 'user_exercise_submissions'
    lesson_progress_table = 'user_lesson_progress'

    # Add new columns to user_exercise_submissions if they don't exist
    if not column_exists(bind, submissions_table, 'code_submitted'):
        op.add_column(submissions_table, sa.Column('code_submitted', sa.Text(), nullable=True))
        op.execute(f"UPDATE {submissions_table} SET code_submitted = '' WHERE code_submitted IS NULL")
        op.alter_column(submissions_table, 'code_submitted', nullable=False)

    if not column_exists(bind, submissions_table, 'passed'):
        op.add_column(submissions_table, sa.Column('passed', sa.Boolean(), nullable=True))

    if not column_exists(bind, submissions_table, 'error_message'):
        op.add_column(submissions_table, sa.Column('error_message', sa.Text(), nullable=True))

    if not column_exists(bind, submissions_table, 'submission_date'):
        op.add_column(submissions_table, sa.Column('submission_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    if not column_exists(bind, submissions_table, 'execution_time'):
        op.add_column(submissions_table, sa.Column('execution_time', sa.Float(), nullable=True))

    # Alter existing column
    if column_exists(bind, submissions_table, 'lesson_id'):
        op.alter_column(submissions_table, 'lesson_id', existing_type=sa.INTEGER(), nullable=True)

    # Drop constraint if it exists
    fk_to_drop = 'user_exercise_submissions_user_progress_id_fkey'
    if constraint_exists(bind, fk_to_drop):
        op.drop_constraint(fk_to_drop, submissions_table, type_='foreignkey')

    # Drop old columns if they exist
    columns_to_drop = ['score', 'attempt_number', 'is_correct', 'execution_time_ms', 'submitted_at', 'user_progress_id', 'submitted_code']
    for col in columns_to_drop:
        if column_exists(bind, submissions_table, col):
            op.drop_column(submissions_table, col)

    # Create new foreign key
    fk_to_create = 'fk_user_lesson_progress_user_id'
    if not constraint_exists(bind, fk_to_create):
        op.create_foreign_key(fk_to_create, lesson_progress_table, 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    submissions_table = 'user_exercise_submissions'
    lesson_progress_table = 'user_lesson_progress'

    # Drop foreign key created in upgrade
    fk_to_drop_downgrade = 'fk_user_lesson_progress_user_id'
    if constraint_exists(bind, fk_to_drop_downgrade):
        op.drop_constraint(fk_to_drop_downgrade, lesson_progress_table, type_='foreignkey')

    # Re-add columns dropped in upgrade
    if not column_exists(bind, submissions_table, 'submitted_code'):
        op.add_column(submissions_table, sa.Column('submitted_code', sa.TEXT(), autoincrement=False, nullable=True))
    if not column_exists(bind, submissions_table, 'user_progress_id'):
        op.add_column(submissions_table, sa.Column('user_progress_id', sa.INTEGER(), autoincrement=False, nullable=True))
    if not column_exists(bind, submissions_table, 'submitted_at'):
        op.add_column(submissions_table, sa.Column('submitted_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=True))
    if not column_exists(bind, submissions_table, 'execution_time_ms'):
        op.add_column(submissions_table, sa.Column('execution_time_ms', sa.INTEGER(), autoincrement=False, nullable=True))
    if not column_exists(bind, submissions_table, 'is_correct'):
        op.add_column(submissions_table, sa.Column('is_correct', sa.BOOLEAN(), server_default='false', autoincrement=False, nullable=False))
    if not column_exists(bind, submissions_table, 'attempt_number'):
        op.add_column(submissions_table, sa.Column('attempt_number', sa.INTEGER(), server_default=sa.text('1'), autoincrement=False, nullable=False))
    if not column_exists(bind, submissions_table, 'score'):
        op.add_column(submissions_table, sa.Column('score', sa.INTEGER(), autoincrement=False, nullable=True))

    # Re-create foreign key dropped in upgrade
    fk_to_recreate = 'user_exercise_submissions_user_progress_id_fkey'
    if not constraint_exists(bind, fk_to_recreate):
        op.create_foreign_key(fk_to_recreate, submissions_table, 'user_progress', ['user_progress_id'], ['id'])

    # Revert altered column
    if column_exists(bind, submissions_table, 'lesson_id'):
        op.alter_column(submissions_table, 'lesson_id', existing_type=sa.INTEGER(), nullable=False)

    # Drop columns added in upgrade
    columns_to_drop_downgrade = ['execution_time', 'submission_date', 'error_message', 'passed', 'code_submitted']
    for col in columns_to_drop_downgrade:
        if column_exists(bind, submissions_table, col):
            op.drop_column(submissions_table, col)
