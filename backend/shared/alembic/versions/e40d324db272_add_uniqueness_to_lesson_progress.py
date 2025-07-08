"""add uniqueness to lesson progress

Revision ID: e40d324db272
Revises: cc3d5eec5ac1
Create Date: 2025-06-22 01:46:12.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'e40d324db272'
down_revision: Union[str, None] = 'cc3d5eec5ac1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def constraint_exists(conn, constraint_name: str, schema: str = 'public') -> bool:
    """Checks if a constraint exists."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = :schema AND constraint_name = :constraint_name
        )
    """)
    return conn.execute(sql, {'schema': schema, 'constraint_name': constraint_name}).scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    constraint_name = 'uq_user_lesson_progress'
    if not constraint_exists(bind, constraint_name):
        # --- ADD THIS BLOCK TO DELETE DUPLICATES ---
        # This SQL statement finds rows with the same user_id and lesson_id,
        # and deletes all but the one with the highest ID (the most recent entry).
        op.execute("""
            DELETE FROM user_lesson_progress a
            USING user_lesson_progress b
            WHERE a.id < b.id
            AND a.user_id = b.user_id
            AND a.lesson_id = b.lesson_id;
        """)
        # --- END OF BLOCK TO ADD ---

        op.create_unique_constraint(constraint_name, 'user_lesson_progress', ['user_id', 'lesson_id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    constraint_name = 'uq_user_lesson_progress'
    if constraint_exists(bind, constraint_name):
        op.drop_constraint(constraint_name, 'user_lesson_progress', type_='unique')
