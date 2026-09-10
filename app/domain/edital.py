# app/domain/edital.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class Fonte(StrEnum):
    PNCP = "pncp"
    COMPRAS_GOV = "compras_gov"


class StatusCaixa(StrEnum):
    NOVO = "novo"
    LIDO = "lido"
    ARQUIVADO = "arquivado"
    OPORTUNIDADE = "oportunidade"


class TipoArquivo(StrEnum):
    EDITAL = "edital"
    TR = "tr"
    ETP = "etp"
    PB = "pb"


@dataclass(frozen=True)
class Edital:
    fonte: Fonte
    chave_natural: str
    objeto: str
    orgao_nome: str
    orgao_cnpj: str
    uf: str | None
    municipio: str | None
    modalidade: str | None
    valor_estimado: Decimal | None
    data_publicacao: date | None
    data_abertura: date | None
    data_fim_propostas: date | None
    url_origem: str
    texto_extra: str = ""


@dataclass(frozen=True)
class ArquivoRef:
    tipo: TipoArquivo
    url: str
    nome: str
