from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, DateTime, Date, Float, ForeignKey, UniqueConstraint, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EditalRow(Base):
    __tablename__ = "edital"
    __table_args__ = (UniqueConstraint("fonte", "chave_natural", name="uq_edital_fonte_chave"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String(20), index=True)
    chave_natural: Mapped[str] = mapped_column(String(200))
    hash_conteudo: Mapped[str] = mapped_column(String(64))
    objeto: Mapped[str] = mapped_column(Text)
    orgao_nome: Mapped[str] = mapped_column(String(300), default="")
    orgao_cnpj: Mapped[str] = mapped_column(String(20), default="")
    uf: Mapped[str | None] = mapped_column(String(2))
    municipio: Mapped[str | None] = mapped_column(String(200))
    modalidade: Mapped[str | None] = mapped_column(String(120))
    valor_estimado: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    data_publicacao: Mapped[datetime | None] = mapped_column(Date, index=True)
    data_abertura: Mapped[datetime | None] = mapped_column(Date)
    data_fim_propostas: Mapped[datetime | None] = mapped_column(Date)
    score_relevancia: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    motivo_relevancia: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="novo", index=True)
    url_origem: Mapped[str] = mapped_column(Text, default="")
    capturado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    arquivos: Mapped[list["ArquivoEditalRow"]] = relationship(
        back_populates="edital", cascade="all, delete-orphan")


class ArquivoEditalRow(Base):
    __tablename__ = "arquivo_edital"
    id: Mapped[int] = mapped_column(primary_key=True)
    edital_id: Mapped[int] = mapped_column(ForeignKey("edital.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20))
    caminho_local: Mapped[str] = mapped_column(Text)
    hash: Mapped[str] = mapped_column(String(64), default="")
    baixado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    edital: Mapped[EditalRow] = relationship(back_populates="arquivos")


class ProjetoInteresseRow(Base):
    __tablename__ = "projeto_interesse"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    palavras_chave: Mapped[list] = mapped_column(JSON, default=list)
    filtros: Mapped[dict] = mapped_column(JSON, default=dict)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExecucaoCapturaRow(Base):
    __tablename__ = "execucao_captura"
    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String(20), index=True)
    janela_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    janela_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_lidos: Mapped[int] = mapped_column(default=0)
    total_novos: Mapped[int] = mapped_column(default=0)
    total_relevantes: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="sucesso")
    erro: Mapped[str] = mapped_column(Text, default="")
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    terminado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DigestLogRow(Base):
    __tablename__ = "digest_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    data_ref: Mapped[datetime] = mapped_column(Date, index=True)
    canais: Mapped[str] = mapped_column(String(120), default="")
    enviado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resumo: Mapped[dict] = mapped_column(JSON, default=dict)
