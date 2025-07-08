"""add_feedback_to_user_exercise_submissions

Revision ID: cf36296cfcaa
Revises: df13caae0fac
Create Date: 2025-06-02 17:39:13.061793

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'cf36296cfcaa'
down_revision: Union[str, None] = 'df13caae0fac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(conn, table_name: str, column_name: str, schema: str = 'public') -> bool:
    """Checks if a column exists in a table."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table_name AND column_name = :column_name
        )
    """)
    return conn.execute(sql, {'schema': schema, 'table_name': table_name, 'column_name': column_name}).scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    table_name = 'user_exercise_submissions'

    if not column_exists(bind, table_name, 'feedback'):
        op.add_column(table_name, sa.Column('feedback', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'user_exercise_submissions'

    if column_exists(bind, table_name, 'feedback'):
        op.drop_column(table_name, 'feedback')
