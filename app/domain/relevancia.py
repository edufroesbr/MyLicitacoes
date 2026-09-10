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


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def classificar_relevancia(objeto: str, texto: str, lexico: Lexico) -> ScoreRelevancia:
    alvo = _norm(f"{objeto} {texto}")
    achados = tuple(t for t in sorted(lexico.positivos) if _norm(t) in alvo)
    neg = sum(1 for t in lexico.negativos if _norm(t) in alvo)
    total = len(lexico.positivos) or 1
    valor = max(0, len(achados) - neg) / total
    return ScoreRelevancia(valor=valor, termos=achados)
