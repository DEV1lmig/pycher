"""add_is_active_enrollment_to_usercourseenrollment

Revision ID: 36b6934da72b
Revises: 484fce812292
Create Date: 2025-07-05 14:46:12.759132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '36b6934da72b'
down_revision: Union[str, None] = '484fce812292'
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
    if not column_exists(bind, 'user_course_enrollments', 'is_active_enrollment'):
        op.add_column('user_course_enrollments',
                    sa.Column('is_active_enrollment', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if column_exists(bind, 'user_course_enrollments', 'is_active_enrollment'):
        op.drop_column('user_course_enrollments', 'is_active_enrollment')
