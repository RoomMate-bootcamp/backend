"""add metadata to user

Revision ID: d363e080604d
Revises: bc063aa68da7
Create Date: 2025-04-18 19:26:29.448464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd363e080604d'
down_revision: Union[str, None] = 'bc063aa68da7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('study_location', sa.String(), nullable=True))
    op.add_column('users', sa.Column('study_program', sa.String(), nullable=True))
    op.add_column('users', sa.Column('accommodation_preference', sa.Enum('APARTMENT', 'DORMITORY', 'NO_PREFERENCE', name='accommodationpreference', native_enum=False), nullable=True))
    op.add_column('users', sa.Column('telegram_username', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'telegram_username')
    op.drop_column('users', 'accommodation_preference')
    op.drop_column('users', 'study_program')
    op.drop_column('users', 'study_location')
    # ### end Alembic commands ###
