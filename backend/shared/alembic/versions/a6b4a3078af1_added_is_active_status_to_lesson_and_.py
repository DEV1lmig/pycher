"""added is_active status to Lesson and Module

Revision ID: a6b4a3078af1
Revises: 2ae7dcb6b687
Create Date: 2025-06-03 10:41:10.411517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6b4a3078af1'
down_revision: Union[str, None] = '2ae7dcb6b687'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lessons', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('modules', sa.Column('is_active', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('modules', 'is_active')
    op.drop_column('lessons', 'is_active')
    # ### end Alembic commands ###
