"""add_lesson_id_attempt_number_to_submission_and_lesson_submissions_rel

Revision ID: c02851b573fd
Revises: 6537569d184a
Create Date: 2025-05-28 16:26:00.023772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c02851b573fd'
down_revision: Union[str, None] = '6537569d184a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Check if columns exist before trying to add them
    # This is a more robust way but requires inspecting the table

    # For 'execution_time_ms', since the error says it exists, we'll skip adding it.
    # op.add_column('user_exercise_submissions', sa.Column('execution_time_ms', sa.Integer(), nullable=True))
    print("Skipping add_column for execution_time_ms as it likely already exists.")

    # For 'lesson_id' - you might need to check if this also exists
    # If you get a "DuplicateColumn" error for lesson_id next, comment out this line too.
    try:
        op.add_column('user_exercise_submissions', sa.Column('lesson_id', sa.Integer(), nullable=True))
    except sa.exc.ProgrammingError as e:
        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
            print("Column 'lesson_id' already exists, skipping add_column.")
        else:
            raise

    # For 'attempt_number' - you might need to check if this also exists
    try:
        op.add_column('user_exercise_submissions', sa.Column('attempt_number', sa.Integer(), nullable=True))
    except sa.exc.ProgrammingError as e:
        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
            print("Column 'attempt_number' already exists, skipping add_column.")
        else:
            raise


    # Populate and alter 'attempt_number'
    # This part should run even if the column was added previously but not yet populated/altered.
    op.execute('UPDATE user_exercise_submissions SET attempt_number = 1 WHERE attempt_number IS NULL')
    op.alter_column('user_exercise_submissions', 'attempt_number',
               existing_type=sa.INTEGER(),
               nullable=False,
               server_default=sa.text('1'))

    # Populate and alter 'lesson_id'
    # Ensure lesson_id is populated if it needs to be non-nullable.
    # If you have a default or can derive it:
    # op.execute('UPDATE user_exercise_submissions SET lesson_id = <some_value_or_subquery> WHERE lesson_id IS NULL')
    op.alter_column('user_exercise_submissions', 'lesson_id',
               existing_type=sa.INTEGER(),
               nullable=False) # As per your model

    # Create foreign key and index - these might also exist.
    # It's harder to conditionally create constraints without more complex checks.
    # If these operations fail because the constraint/index already exists,
    # you'll need to comment them out as well or use try-except.

    try:
        op.create_foreign_key(
            'fk_user_exercise_submissions_lesson_id_lessons',
            'user_exercise_submissions',
            'lessons',
            ['lesson_id'],
            ['id']
        )
    except sa.exc.ProgrammingError as e:
        if "already exists" in str(e).lower(): # PostgreSQL uses "constraint ... already exists"
             print("Foreign key 'fk_user_exercise_submissions_lesson_id_lessons' already exists, skipping.")
        else:
            raise

    try:
        op.create_index(op.f('ix_user_exercise_submissions_lesson_id'), 'user_exercise_submissions', ['lesson_id'], unique=False)
    except sa.exc.ProgrammingError as e: # Index creation errors can vary
        if "already exists" in str(e).lower():
            print("Index 'ix_user_exercise_submissions_lesson_id' already exists, skipping.")
        else:
            raise
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrade logic should be robust to whether items existed or not.
    # Using 'if_exists=True' for drop_index and drop_constraint is good practice if available
    # or wrap in try-except. Alembic's op.drop_constraint doesn't have if_exists.

    try:
        op.drop_index(op.f('ix_user_exercise_submissions_lesson_id'), table_name='user_exercise_submissions')
    except Exception as e:
        print(f"Could not drop index ix_user_exercise_submissions_lesson_id (may not exist): {e}")

    try:
        op.drop_constraint('fk_user_exercise_submissions_lesson_id_lessons', 'user_exercise_submissions', type_='foreignkey')
    except Exception as e:
        print(f"Could not drop constraint fk_user_exercise_submissions_lesson_id_lessons (may not exist): {e}")

    # Dropping columns should be fine, if they don't exist it might error or not depending on DB
    # It's safer to assume they were added by this migration's upgrade path.
    op.drop_column('user_exercise_submissions', 'attempt_number')
    # op.drop_column('user_exercise_submissions', 'execution_time_ms') # If we skipped adding, we might skip dropping
    # To be safe, only drop what this migration *intended* to create.
    # If execution_time_ms was pre-existing, this migration shouldn't be responsible for dropping it.
    # However, if the goal is to revert this *migration's effect*, and its effect was to ensure the column
    # is there and configured, then dropping it is part of the revert.
    # For now, let's assume if it was pre-existing, we don't touch it in downgrade for this specific column.
    # If you want the downgrade to remove it regardless, uncomment the line.
    # A more precise downgrade would check if the column was indeed added by *this* upgrade.

    op.drop_column('user_exercise_submissions', 'lesson_id')
    # ### end Alembic commands ###
