# tests/domain/test_relevancia.py
from app.domain.relevancia import classificar_relevancia, Lexico, ScoreRelevancia

LX = Lexico(
    positivos=frozenset({"clipping", "monitoramento de publicacoes", "diario de justica", "dje"}),
    negativos=frozenset({"merenda escolar"}),
)


def test_objeto_tipo_lexflow_pontua_alto():
    s = classificar_relevancia("Contratação de CLIPPING e monitoramento de publicações", "", LX)
    assert isinstance(s, ScoreRelevancia)
    assert s.valor >= 0.5
    assert "clipping" in s.termos


def test_objeto_irrelevante_pontua_zero():
    s = classificar_relevancia("Aquisição de merenda escolar", "para as escolas", LX)
    assert s.valor == 0.0


def test_acentos_e_caixa_nao_importam():
    s = classificar_relevancia("DIÁRIO DE JUSTIÇA eletrônico", "", LX)
    assert "diario de justica" in s.termos
