"""add is_Active course enrollments

Revision ID: edf047a461e3
Revises: 59eced616f19
Create Date: 2025-07-08 18:22:27.002122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'edf047a461e3'
down_revision: Union[str, None] = '59eced616f19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Añadir columna solo si no existe
    columns = [col['name'] for col in inspector.get_columns('user_course_enrollments')]
    if 'is_active' not in columns:
        op.add_column('user_course_enrollments', sa.Column('is_active', sa.Boolean(), nullable=True))

    # Eliminar constraint solo si existe
    constraints = [c['name'] for c in inspector.get_foreign_keys('user_lesson_progress')]
    fk_name = op.f('fk_user_lesson_progress_user_id')
    if fk_name in constraints:
        op.drop_constraint(fk_name, 'user_lesson_progress', type_='foreignkey')

    # Alterar columnas solo si existen
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'first_name' in user_columns:
        
        op.alter_column('users', 'first_name',
            existing_type=sa.VARCHAR(),
            nullable=True,
            existing_server_default=sa.text("''::character varying"))
    if 'last_name' in user_columns:
        op.alter_column('users', 'last_name',
            existing_type=sa.VARCHAR(),
            nullable=True,
            existing_server_default=sa.text("''::character varying"))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    user_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'last_name' in user_columns:
        op.alter_column('users', 'last_name',
            existing_type=sa.VARCHAR(),
            nullable=False,
            existing_server_default=sa.text("''::character varying"))
    if 'first_name' in user_columns:
        op.alter_column('users', 'first_name',
            existing_type=sa.VARCHAR(),
            nullable=False,
            existing_server_default=sa.text("''::character varying"))

    # Crear constraint solo si no existe
    constraints = [c['name'] for c in inspector.get_foreign_keys('user_lesson_progress')]
    fk_name = op.f('fk_user_lesson_progress_user_id')
    if fk_name not in constraints:
        op.create_foreign_key(fk_name, 'user_lesson_progress', 'users', ['user_id'], ['id'])

    # Eliminar columna solo si existe
    columns = [col['name'] for col in inspector.get_columns('user_course_enrollments')]
    if 'is_active' in columns:
        op.drop_column('user_course_enrollments', 'is_active')
