# app/domain/digest.py
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from app.domain.edital import Edital


@dataclass(frozen=True)
class LinhaProjeto:
    nome: str
    novos: int
    prazo_a_fechar: int


@dataclass(frozen=True)
class Digest:
    data_ref: date
    total_novos: int
    total_relevantes: int
    total_downloads: int
    fontes_com_falha: tuple[str, ...]
    destaques: tuple[Edital, ...]
    projetos: tuple[LinhaProjeto, ...]


def montar_digest(data_ref: date, relevantes: Sequence[Edital], novos_total: int,
                  downloads: int, fontes_falha: Sequence[str],
                  projetos_linhas: Sequence[LinhaProjeto], max_destaques: int = 10) -> Digest:
    return Digest(
        data_ref=data_ref,
        total_novos=novos_total,
        total_relevantes=len(relevantes),
        total_downloads=downloads,
        fontes_com_falha=tuple(fontes_falha),
        destaques=tuple(relevantes[:max_destaques]),
        projetos=tuple(projetos_linhas),
    )
