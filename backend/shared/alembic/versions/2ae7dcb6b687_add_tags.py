"""add_tags

Revision ID: 2ae7dcb6b687
Revises: 2a04fdeff7cd
Create Date: 2025-06-02 19:45:48.104819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2ae7dcb6b687'
down_revision: Union[str, None] = '2a04fdeff7cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercises', sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('exercises', 'tags')
    # ### end Alembic commands ###
