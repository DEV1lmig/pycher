"""add_last_accessed_exercise_id_to_user_lesson_progress

Revision ID: 45ccc403761d
Revises: 5d8b23417d0d
Create Date: 2025-07-05 14:51:12.345678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '45ccc403761d'
down_revision: Union[str, None] = '5d8b23417d0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, table_name: str, column_name: str, schema: str = 'public') -> bool:
    """Checks if a column exists in a table."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table_name
              AND column_name = :column_name
        )
    """)
    result = conn.execute(sql, {'schema': schema, 'table_name': table_name, 'column_name': column_name})
    return result.scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if not column_exists(bind, 'user_lesson_progress', 'last_accessed_exercise_id'):
        op.add_column('user_lesson_progress',
                    sa.Column('last_accessed_exercise_id', sa.Integer(), nullable=True))
    try:
        op.create_foreign_key(
            'fk_user_lesson_progress_last_accessed_exercise_id',
            'user_lesson_progress', 'exercises',
            ['last_accessed_exercise_id'], ['id']
        )
    except Exception:
        # Foreign key might already exist
        pass


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    try:
        op.drop_constraint('fk_user_lesson_progress_last_accessed_exercise_id', 'user_lesson_progress', type_='foreignkey')
    except Exception:
        # Constraint might not exist
        pass
    if column_exists(bind, 'user_lesson_progress', 'last_accessed_exercise_id'):
        op.drop_column('user_lesson_progress', 'last_accessed_exercise_id')
