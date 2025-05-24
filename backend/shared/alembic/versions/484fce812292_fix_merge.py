"""fix merge

Revision ID: 484fce812292
Revises: a10e133c90c2, 880b3c854d4b
Create Date: 2025-05-24 17:57:08.266354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '484fce812292'
down_revision: Union[str, None] = ('a10e133c90c2', '880b3c854d4b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
