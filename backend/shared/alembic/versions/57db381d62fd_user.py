"""user - initial user table setup or additions

Revision ID: 57db381d62fd
Revises: # Set this to the ID of the migration before this one, or None if it's the first.
Create Date: 2025-05-14 11:05:49.233038 # Or your original create date

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text # For executing raw SQL checks


# revision identifiers, used by Alembic.
revision: str = '57db381d62fd'
# IMPORTANT: Ensure 'down_revision' is correctly set.
# If this was the very first migration, it's None. Otherwise, it's the ID of the previous migration.
down_revision: Union[str, None] = None # For example, if it's the first migration. Adjust if not.
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

# If this migration also created tables or other constraints, you'd add helpers like:
# def table_exists(conn, table_name: str, schema: str = 'public') -> bool: ...
# def constraint_exists(conn, constraint_name: str, schema: str = 'public') -> bool: ...

def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Add 'first_name' to 'users' table if it doesn't exist
    if not column_exists(bind, 'users', 'first_name'):
        # When adding a non-nullable column to an existing table,
        # provide a server_default or ensure existing rows are handled.
        op.add_column('users', sa.Column('first_name', sa.String(), nullable=False, server_default=''))
    else:
        # Optional: If it exists, you might want to ensure its properties are correct.
        # For example, ensure it's not nullable.
        op.alter_column('users', 'first_name', existing_type=sa.String(), nullable=False, server_default='')


    # Add 'last_name' to 'users' table if it doesn't exist
    if not column_exists(bind, 'users', 'last_name'):
        op.add_column('users', sa.Column('last_name', sa.String(), nullable=False, server_default=''))
    else:
        op.alter_column('users', 'last_name', existing_type=sa.String(), nullable=False, server_default='')

    # --- Handle other columns this migration might have added ---
    # Example for 'email'
    # if not column_exists(bind, 'users', 'email'):
    #     op.add_column('users', sa.Column('email', sa.String(), nullable=False, unique=True, index=True))
    # else:
    #     # Ensure properties like unique and index if necessary
    #     # op.alter_column('users', 'email', existing_type=sa.String(), nullable=False)
    #     # if not index_exists(bind, 'ix_users_email', 'users'): # Requires index_exists helper
    #     #     op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    #     pass # Or ensure other properties

    # Example for 'hashed_password'
    # if not column_exists(bind, 'users', 'hashed_password'):
    #     op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=False))
    # else:
    #     op.alter_column('users', 'hashed_password', existing_type=sa.String(), nullable=False)

    # Example for 'created_at'
    # if not column_exists(bind, 'users', 'created_at'):
    #     op.add_column('users', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    # else:
    #     op.alter_column('users', 'created_at', existing_type=sa.DateTime(), server_default=sa.func.now(), nullable=False)

    # Example for 'is_active'
    # if not column_exists(bind, 'users', 'is_active'):
    #     op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False))
    # else:
    #     op.alter_column('users', 'is_active', existing_type=sa.Boolean(), server_default=sa.true(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    # if column_exists(bind, 'users', 'is_active'):
    #     op.drop_column('users', 'is_active')
    # if column_exists(bind, 'users', 'created_at'):
    #     op.drop_column('users', 'created_at')
    # if column_exists(bind, 'users', 'hashed_password'):
    #     op.drop_column('users', 'hashed_password')
    # if column_exists(bind, 'users', 'email'):
    #     # if index_exists(bind, 'ix_users_email', 'users'): # Requires index_exists helper
    #     #     op.drop_index(op.f('ix_users_email'), table_name='users')
    #     op.drop_column('users', 'email')
    if column_exists(bind, 'users', 'last_name'):
        op.drop_column('users', 'last_name')
    if column_exists(bind, 'users', 'first_name'):
        op.drop_column('users', 'first_name')

    # If this migration created the 'users' table, the downgrade would be:
    # if table_exists(bind, 'users'):
    # op.drop_table('users')
