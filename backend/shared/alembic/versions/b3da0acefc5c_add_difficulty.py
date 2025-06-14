"""add_difficulty

Revision ID: b3da0acefc5c
Revises: cf36296cfcaa
Create Date: 2025-06-02 19:43:23.568714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3da0acefc5c'
down_revision: Union[str, None] = 'cf36296cfcaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercises', sa.Column('difficulty', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('exercises', 'difficulty')
    # ### end Alembic commands ###
