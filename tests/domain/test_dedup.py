# tests/domain/test_dedup.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte
from app.domain.dedup import deduplicar, hash_conteudo


def _ed(fonte, chave, objeto="Servico de clipping", cnpj="00000000000191", pub=date(2026, 9, 1)):
    return Edital(fonte, chave, objeto, "Org", cnpj, "AM", "Manaus", "Pregao",
                  Decimal("1"), pub, None, None, "http://x")


def test_dedup_por_chave_natural():
    a = _ed(Fonte.PNCP, "k1")
    b = _ed(Fonte.PNCP, "k1")
    assert len(deduplicar([a, b])) == 1


def test_dedup_entre_fontes_prefere_pncp():
    p = _ed(Fonte.PNCP, "kp")
    c = _ed(Fonte.COMPRAS_GOV, "kc")
    out = deduplicar([c, p])
    assert len(out) == 1
    assert out[0].fonte == Fonte.PNCP


def test_hash_muda_com_conteudo():
    assert hash_conteudo(_ed(Fonte.PNCP, "k", objeto="A")) != hash_conteudo(_ed(Fonte.PNCP, "k", objeto="B"))


def test_sem_cnpj_nao_colapsa_mesmo_objeto_e_data():
    a = _ed(Fonte.COMPRAS_GOV, "kc-1", objeto="Pregao padrao X", cnpj="")
    b = _ed(Fonte.COMPRAS_GOV, "kc-2", objeto="Pregao padrao X", cnpj="")
    out = deduplicar([a, b])
    assert len(out) == 2  # sem CNPJ nao ha colapso entre fontes
