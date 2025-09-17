"""dios mio ya

Revision ID: df13caae0fac
Revises: 15cbd3e65919
Create Date: 2025-05-29 18:58:49.061348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'df13caae0fac'
down_revision: Union[str, None] = '15cbd3e65919'
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
    column_name = 'attempt_number'
    if not column_exists(bind, table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    table_name = 'user_exercise_submissions'
    column_name = 'attempt_number'
    if column_exists(bind, table_name, column_name):
        op.drop_column(table_name, column_name)
