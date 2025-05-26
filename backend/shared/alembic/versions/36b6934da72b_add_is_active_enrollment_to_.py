"""add_is_active_enrollment_to_usercourseenrollment

Revision ID: 36b6934da72b
Revises: 484fce812292
Create Date: 2025-05-25 13:30:51.233442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36b6934da72b'
down_revision: Union[str, None] = '484fce812292'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user_course_enrollments',
                  sa.Column('is_active_enrollment', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    # Update existing rows to set the new column to true where it's currently NULL (after column addition)
    # This ensures existing enrollments are considered active by default.
    op.execute('UPDATE user_course_enrollments SET is_active_enrollment = true WHERE is_active_enrollment IS NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_course_enrollments', 'is_active_enrollment')
