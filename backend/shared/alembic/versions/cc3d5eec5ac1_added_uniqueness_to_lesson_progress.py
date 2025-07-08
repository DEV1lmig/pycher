"""added uniqueness to lesson progress

Revision ID: cc3d5eec5ac1
Revises: 56a69af77c45
Create Date: 2025-06-22 01:45:27.937709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc3d5eec5ac1'
down_revision: Union[str, None] = '56a69af77c45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    try:
        op.drop_constraint('user_lesson_progress_user_id_fkey', 'user_lesson_progress', type_='foreignkey')
    except Exception:
        # Constraint may not exist or have a different name, ignore.
        pass

    # Create with a predictable name to make it idempotent
    op.create_foreign_key('fk_user_lesson_progress_user_id_cascade', 'user_lesson_progress', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    try:
        op.drop_constraint('fk_user_lesson_progress_user_id_cascade', 'user_lesson_progress', type_='foreignkey')
    except Exception:
        # Constraint may not exist, ignore.
        pass

    # Recreate the original foreign key without cascade
    op.create_foreign_key('user_lesson_progress_user_id_fkey', 'user_lesson_progress', 'users', ['user_id'], ['id'])
