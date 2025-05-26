"""add_is_active_enrollment_to_usercourseenrollment2

Revision ID: b3f10a737b76
Revises: 36b6934da72b
Create Date: 2025-05-25 14:02:38.703135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f10a737b76'
down_revision: Union[str, None] = '36b6934da72b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
