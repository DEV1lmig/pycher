"""Add unique constraint to user_lesson_progress

Revision ID: 9c12f7a2501e
Revises: cc3d5eec5ac1
Create Date: 2025-06-22 02:05:24.768000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c12f7a2501e'
down_revision: Union[str, None] = 'cc3d5eec5ac1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if the constraint already exists before creating it
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing unique constraints on the table
    unique_constraints = inspector.get_unique_constraints('user_lesson_progress')
    constraint_names = [uc['name'] for uc in unique_constraints]

    # Only create the constraint if it doesn't already exist
    if 'uq_user_lesson_progress' not in constraint_names:
        op.create_unique_constraint('uq_user_lesson_progress', 'user_lesson_progress', ['user_id', 'lesson_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Check if the constraint exists before trying to drop it
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing unique constraints on the table
    unique_constraints = inspector.get_unique_constraints('user_lesson_progress')
    constraint_names = [uc['name'] for uc in unique_constraints]

    # Only drop the constraint if it exists
    if 'uq_user_lesson_progress' in constraint_names:
        op.drop_constraint('uq_user_lesson_progress', 'user_lesson_progress', type_='unique')
