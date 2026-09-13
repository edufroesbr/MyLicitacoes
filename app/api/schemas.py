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


class EditalDetalhe(EditalResumo):
    orgao_cnpj: str
    municipio: str | None
    motivo_relevancia: str
    url_origem: str
    arquivos: list[ArquivoResumo] = []


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
