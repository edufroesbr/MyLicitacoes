# app/domain/relevancia.py
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Lexico:
    positivos: frozenset[str]
    negativos: frozenset[str]


@dataclass(frozen=True)
class ScoreRelevancia:
    valor: float
    termos: tuple[str, ...]


MASSA_ALVO_RELEVANCIA = 3
"""Numero de termos-alvo para normalizar o score, independente do tamanho do
lexico. Fixo (nao len(lexico.positivos)): crescer o lexico com sinonimos nao
pode baixar o score de ninguem, e o piso (0.34) tem de continuar comparavel
entre lexicos de tamanhos diferentes."""


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def classificar_relevancia(objeto: str, texto: str, lexico: Lexico) -> ScoreRelevancia:
    alvo = _norm(f"{objeto} {texto}")
    achados = tuple(t for t in sorted(lexico.positivos) if _norm(t) in alvo)
    neg = sum(1 for t in lexico.negativos if _norm(t) in alvo)
    valor = min(1.0, max(0, len(achados) - neg) / MASSA_ALVO_RELEVANCIA)
    return ScoreRelevancia(valor=valor, termos=achados)
