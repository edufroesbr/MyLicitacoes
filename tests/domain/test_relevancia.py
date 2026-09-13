# tests/domain/test_relevancia.py
from app.domain.relevancia import classificar_relevancia, Lexico, ScoreRelevancia
from app.domain.lexico import LEXICO_TIPO_LEXFLOW

PISO_REAL = 0.34  # app.config.Settings().score_piso; evita instanciar Settings sem env

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


def test_caso_canonico_lexflow_passa_o_piso_real_com_o_lexico_real():
    """Guard de calibracao: o objeto canonico do LexFlow (2 termos: clipping +
    monitoramento de publicacoes) tem de qualificar contra o piso real
    (0.34), mesmo com o lexico real de 14 termos. Antes do fix, o score era
    normalizado por len(lexico.positivos) (14) e 2/14=0.14 REJEITAVA o caso
    canonico."""
    s = classificar_relevancia(
        "Contratação de clipping e monitoramento de publicações", "", LEXICO_TIPO_LEXFLOW)
    assert s.valor >= PISO_REAL


def test_caso_irrelevante_nao_passa_o_piso_real_com_o_lexico_real():
    s = classificar_relevancia("aquisição de merenda escolar", "", LEXICO_TIPO_LEXFLOW)
    assert s.valor < PISO_REAL
