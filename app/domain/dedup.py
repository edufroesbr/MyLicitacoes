# app/domain/dedup.py
import hashlib
import unicodedata
from collections.abc import Iterable
from app.domain.edital import Edital, Fonte


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def hash_conteudo(e: Edital) -> str:
    base = f"{e.objeto}|{e.orgao_cnpj}|{e.data_publicacao}|{e.data_abertura}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def deduplicar(editais: Iterable[Edital]) -> list[Edital]:
    por_chave: dict[tuple[Fonte, str], Edital] = {}
    for e in editais:
        por_chave[(e.fonte, e.chave_natural)] = e
    entre_fontes: dict[tuple[str, str, object], Edital] = {}
    for e in por_chave.values():
        k = (e.orgao_cnpj, _norm(e.objeto), e.data_publicacao)
        atual = entre_fontes.get(k)
        if atual is None or (e.fonte == Fonte.PNCP and atual.fonte != Fonte.PNCP):
            entre_fontes[k] = e
    return list(entre_fontes.values())
