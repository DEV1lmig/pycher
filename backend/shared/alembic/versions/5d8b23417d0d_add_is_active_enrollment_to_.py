"""add_is_active_enrollment_to_usercourseenrollment_final

Revision ID: 5d8b23417d0d
Revises: b3f10a737b76
Create Date: 2025-05-25 14:03:26.273884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d8b23417d0d'
down_revision: Union[str, None] = 'b3f10a737b76'
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
