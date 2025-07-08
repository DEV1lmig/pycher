"""diosmio ya

Revision ID: 901030a37341
Revises: a6b4a3078af1
Create Date: 2025-06-04 09:50:22.968003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '901030a37341'
down_revision: Union[str, None] = 'a6b4a3078af1'
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
    constraint_name = 'uq_user_module_progress'
    if not constraint_exists(bind, constraint_name):
        op.create_unique_constraint(constraint_name, 'user_module_progress', ['user_id', 'module_id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    constraint_name = 'uq_user_module_progress'
    if constraint_exists(bind, constraint_name):
        op.drop_constraint(constraint_name, 'user_module_progress', type_='unique')
