"""added course id to execerices

Revision ID: 44a5ef4c3573
Revises: d0887f6625a7
Create Date: 2025-06-06 12:29:42.082752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44a5ef4c3573'
down_revision: Union[str, None] = 'd0887f6625a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercises', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'exercises', 'courses', ['course_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'exercises', type_='foreignkey')
    op.drop_column('exercises', 'course_id')
    # ### end Alembic commands ###
