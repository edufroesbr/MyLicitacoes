"""unaccent extension + edital.situacao_compra

Revision ID: unaccent_situacao_20261008
Revises: inicial_edital_20260910
Create Date: 2026-10-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'unaccent_situacao_20261008'
down_revision: Union[str, Sequence[str], None] = 'inicial_edital_20260910'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.add_column('edital', sa.Column('situacao_compra', sa.String(length=60), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('edital', 'situacao_compra')
    op.execute("DROP EXTENSION IF EXISTS unaccent")
