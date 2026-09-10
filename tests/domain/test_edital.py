# tests/domain/test_edital.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte, StatusCaixa


def test_edital_e_imutavel_e_tem_chave():
    e = Edital(
        fonte=Fonte.PNCP, chave_natural="00000000000191-2026-42",
        objeto="Contratacao de servico de clipping", orgao_nome="TJ",
        orgao_cnpj="00000000000191", uf="AM", municipio="Manaus",
        modalidade="Pregao", valor_estimado=Decimal("1000"),
        data_publicacao=date(2026, 9, 1), data_abertura=None,
        data_fim_propostas=None, url_origem="https://pncp.gov.br/x",
    )
    assert e.fonte == Fonte.PNCP
    assert StatusCaixa.NOVO == "novo"
    import dataclasses
    try:
        e.objeto = "x"  # frozen
        assert False
    except dataclasses.FrozenInstanceError:
        pass
