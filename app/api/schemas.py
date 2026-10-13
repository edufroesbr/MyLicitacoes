from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from app.domain.edital import StatusCaixa


class EditalResumo(BaseModel):
    id: int
    fonte: str
    objeto: str
    orgao_nome: str
    uf: str | None
    modalidade: str | None
    valor_estimado: Decimal | None
    data_publicacao: date | None
    data_fim_propostas: date | None
    score_relevancia: float
    status: str
    model_config = {"from_attributes": True}


class Pagina(BaseModel):
    itens: list[EditalResumo]
    total: int
    pagina: int
    tamanho: int


class ArquivoResumo(BaseModel):
    id: int
    tipo: str
    model_config = {"from_attributes": True}


class ArquivoCatalogo(BaseModel):
    """Documento conhecido na fonte original mas nao baixado/guardado por
    nos (editais fora do piso de relevancia nao disparam download
    automatico) - o link aponta direto pra fonte, nao pro nosso proxy."""
    tipo: str
    nome: str
    url: str


class ContratoResumo(BaseModel):
    numero_contrato: str
    fornecedor_nome: str
    fornecedor_documento: str
    valor_global: Decimal | None
    data_assinatura: date | None
    model_config = {"from_attributes": True}


class EditalDetalhe(EditalResumo):
    orgao_cnpj: str
    municipio: str | None
    motivo_relevancia: str
    url_origem: str
    situacao_compra: str | None = None
    arquivos: list[ArquivoResumo] = []
    arquivos_catalogo: list[ArquivoCatalogo] = []
    contratos: list[ContratoResumo] = []


class MudarStatus(BaseModel):
    status: StatusCaixa


class ProjetoIn(BaseModel):
    nome: str
    palavras_chave: list[str] = []
    filtros: dict = {}
    ativo: bool = True


class ProjetoOut(ProjetoIn):
    id: int
    criado_em: datetime
    model_config = {"from_attributes": True}


class ResumoUf(BaseModel):
    uf: str | None
    quantidade: int
    valor_total: Decimal


class ResumoProjeto(BaseModel):
    editais_ativos: int
    editais_encerrados: int
    contratos_quantidade: int
    contratos_valor_total: Decimal
    contratos_valor_medio: Decimal | None
    por_uf: list[ResumoUf]


class PerfilSchema(BaseModel):
    id: int
    nome: str
    email_digest: str | None
    telegram_chat_id: str | None
    receber_email: bool
    receber_telegram: bool
    atualizado_em: datetime
    model_config = {"from_attributes": True}


class PerfilUpdate(BaseModel):
    nome: str
    email_digest: str | None
    telegram_chat_id: str | None
    receber_email: bool
    receber_telegram: bool
