# tests/domain/test_digest.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte
from app.domain.digest import montar_digest, LinhaProjeto


def _ed(o):
    return Edital(Fonte.PNCP, o, o, "Org", "00000000000191", "AM", "Manaus",
                  "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")


def test_digest_conta_e_limita_destaques():
    rel = [_ed(f"clipping {i}") for i in range(15)]
    d = montar_digest(date(2026, 9, 1), rel, novos_total=40, downloads=15,
                      fontes_falha=("compras_gov",),
                      projetos_linhas=[LinhaProjeto("DJE Nordeste", 3, 1)])
    assert d.total_relevantes == 15
    assert d.total_novos == 40
    assert len(d.destaques) == 10
    assert d.fontes_com_falha == ("compras_gov",)
    assert d.projetos[0].nome == "DJE Nordeste"
