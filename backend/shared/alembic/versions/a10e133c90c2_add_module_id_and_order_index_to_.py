"""Add module_id and order_index to exercises

Revision ID: a10e133c90c2
Revises: 57db381d62fd
Create Date: 2025-05-19 11:30:44.671741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a10e133c90c2'
down_revision: Union[str, None] = '57db381d62fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercises', sa.Column('module_id', sa.Integer(), nullable=True))
    op.add_column('exercises', sa.Column('order_index', sa.Integer(), nullable=False))
    op.add_column('exercises', sa.Column('hints', sa.Text(), nullable=True))
    op.alter_column('exercises', 'lesson_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_foreign_key(None, 'exercises', 'modules', ['module_id'], ['id'])
    op.drop_column('exercises', 'points')
    op.drop_column('exercises', 'difficulty')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercises', sa.Column('difficulty', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('exercises', sa.Column('points', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'exercises', type_='foreignkey')
    op.alter_column('exercises', 'lesson_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('exercises', 'hints')
    op.drop_column('exercises', 'order_index')
    op.drop_column('exercises', 'module_id')
    # ### end Alembic commands ###
