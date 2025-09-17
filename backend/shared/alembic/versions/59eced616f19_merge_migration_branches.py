"""Merge migration branches

Revision ID: 59eced616f19
Revises: 2463bd472c8e, 9c12f7a2501e
Create Date: 2025-07-08 16:10:29.118480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59eced616f19'
down_revision: Union[str, None] = ('2463bd472c8e', '9c12f7a2501e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
