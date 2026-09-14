# tests/adapters/test_classificador_keyword.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte
from app.domain.lexico import LEXICO_TIPO_LEXFLOW
from app.adapters.classificador.keyword import KeywordClassificador


def test_keyword_classificador_usa_lexico():
    c = KeywordClassificador(LEXICO_TIPO_LEXFLOW)
    e = Edital(Fonte.PNCP, "k", "Servico de clipping e DJE", "Org", "00000000000191",
               "AM", "Manaus", "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")
    s = c.classificar(e)
    assert s.valor > 0
    assert "clipping" in s.termos
