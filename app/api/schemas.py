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


class EditalDetalhe(EditalResumo):
    orgao_cnpj: str
    municipio: str | None
    motivo_relevancia: str
    url_origem: str
    situacao_compra: str | None = None
    arquivos: list[ArquivoResumo] = []
    arquivos_catalogo: list[ArquivoCatalogo] = []


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
