"""contrato

Revision ID: 41e77b2f0a91
Revises: a333b3f8f4da
Create Date: 2026-10-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41e77b2f0a91'
down_revision: Union[str, Sequence[str], None] = 'a333b3f8f4da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('contrato',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fonte', sa.String(length=20), nullable=False),
    sa.Column('chave_natural', sa.String(length=200), nullable=False),
    sa.Column('edital_id', sa.Integer(), nullable=False),
    sa.Column('numero_contrato', sa.String(length=60), nullable=False),
    sa.Column('fornecedor_nome', sa.String(length=300), nullable=False),
    sa.Column('fornecedor_documento', sa.String(length=20), nullable=False),
    sa.Column('valor_inicial', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('valor_global', sa.Numeric(precision=18, scale=2), nullable=True),
    sa.Column('data_assinatura', sa.Date(), nullable=True),
    sa.Column('data_publicacao', sa.Date(), nullable=True),
    sa.Column('capturado_em', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['edital_id'], ['edital.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fonte', 'chave_natural', name='uq_contrato_fonte_chave')
    )
    op.create_index(op.f('ix_contrato_fonte'), 'contrato', ['fonte'], unique=False)
    op.create_index(op.f('ix_contrato_edital_id'), 'contrato', ['edital_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_contrato_edital_id'), table_name='contrato')
    op.drop_index(op.f('ix_contrato_fonte'), table_name='contrato')
    op.drop_table('contrato')
