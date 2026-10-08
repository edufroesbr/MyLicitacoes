"""perfil

Revision ID: a333b3f8f4da
Revises: unaccent_situacao_20261008
Create Date: 2026-10-08 19:33:49.234166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a333b3f8f4da'
down_revision: Union[str, Sequence[str], None] = 'unaccent_situacao_20261008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('perfil',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('email_digest', sa.String(length=200), nullable=True),
    sa.Column('telegram_chat_id', sa.String(length=60), nullable=True),
    sa.Column('receber_email', sa.Boolean(), nullable=False),
    sa.Column('receber_telegram', sa.Boolean(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('perfil')
