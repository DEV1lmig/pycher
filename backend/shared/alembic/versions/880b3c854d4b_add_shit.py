"""add_shit - comprehensive update for users.updated_at and user_course_enrollments access tracking

Revision ID: 880b3c854d4b
Revises:
Create Date: 2025-05-24 16:45:52.744717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text # For executing raw SQL checks


# revision identifiers, used by Alembic.
revision: str = '880b3c854d4b'
down_revision: Union[str, None] = None # Set this to your actual previous migration ID
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

def constraint_exists(conn, constraint_name: str, schema: str = 'public') -> bool:
    """Checks if a constraint exists."""
    sql = text(f"""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = :schema
              AND constraint_name = :constraint_name
        )
    """)
    result = conn.execute(sql, {'schema': schema, 'constraint_name': constraint_name})
    return result.scalar_one()


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # 1. Add 'updated_at' to 'users' table
    if not column_exists(bind, 'users', 'updated_at'):
        op.add_column('users', sa.Column('updated_at', sa.DateTime(),
                                           server_default=sa.func.now(),
                                           onupdate=sa.func.now(),
                                           nullable=True)) # Add as nullable first
        # Backfill existing rows. Use created_at if available, otherwise current time.
        op.execute("UPDATE users SET updated_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL")
        op.alter_column('users', 'updated_at', nullable=False) # Then make it non-nullable
    else:
        # Ensure it's not nullable if it exists but was nullable
        # This requires inspecting the column's nullable property, which is more complex.
        # For now, we assume if it exists, its properties are as desired or handled by other means.
        # A simple alter_column can be used if you are sure it should be non-nullable.
        # op.alter_column('users', 'updated_at', nullable=False) # Uncomment if needed and safe
        pass


    # 2. Add 'last_accessed_module_id' to 'user_course_enrollments' table
    if not column_exists(bind, 'user_course_enrollments', 'last_accessed_module_id'):
        op.add_column('user_course_enrollments', sa.Column('last_accessed_module_id', sa.Integer(), nullable=True))

    # 3. Add 'last_accessed_lesson_id' to 'user_course_enrollments' table
    if not column_exists(bind, 'user_course_enrollments', 'last_accessed_lesson_id'):
        op.add_column('user_course_enrollments', sa.Column('last_accessed_lesson_id', sa.Integer(), nullable=True))

    # 4. Add Foreign Key for last_accessed_module_id
    fk_module_name = op.f('fk_user_course_enrollments_last_accessed_module_id_modules')
    if column_exists(bind, 'user_course_enrollments', 'last_accessed_module_id') and \
       not constraint_exists(bind, fk_module_name):
        op.create_foreign_key(
            fk_module_name,
            'user_course_enrollments', 'modules',
            ['last_accessed_module_id'], ['id']
        )

    # 5. Add Foreign Key for last_accessed_lesson_id
    fk_lesson_name = op.f('fk_user_course_enrollments_last_accessed_lesson_id_lessons')
    if column_exists(bind, 'user_course_enrollments', 'last_accessed_lesson_id') and \
       not constraint_exists(bind, fk_lesson_name):
        op.create_foreign_key(
            fk_lesson_name,
            'user_course_enrollments', 'lessons',
            ['last_accessed_lesson_id'], ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    # 5. Drop Foreign Key for last_accessed_lesson_id
    fk_lesson_name = op.f('fk_user_course_enrollments_last_accessed_lesson_id_lessons')
    if constraint_exists(bind, fk_lesson_name):
        op.drop_constraint(fk_lesson_name, 'user_course_enrollments', type_='foreignkey')

    # 4. Drop Foreign Key for last_accessed_module_id
    fk_module_name = op.f('fk_user_course_enrollments_last_accessed_module_id_modules')
    if constraint_exists(bind, fk_module_name):
        op.drop_constraint(fk_module_name, 'user_course_enrollments', type_='foreignkey')

    # 3. Drop 'last_accessed_lesson_id' from 'user_course_enrollments' table
    if column_exists(bind, 'user_course_enrollments', 'last_accessed_lesson_id'):
        op.drop_column('user_course_enrollments', 'last_accessed_lesson_id')

    # 2. Drop 'last_accessed_module_id' from 'user_course_enrollments' table
    if column_exists(bind, 'user_course_enrollments', 'last_accessed_module_id'):
        op.drop_column('user_course_enrollments', 'last_accessed_module_id')

    # 1. Drop 'updated_at' from 'users' table
    if column_exists(bind, 'users', 'updated_at'):
        op.drop_column('users', 'updated_at')
