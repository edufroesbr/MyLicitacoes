from datetime import date
from decimal import Decimal
from pydantic import BaseModel


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
