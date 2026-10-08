# tests/adapters/test_pncp.py
import json
from datetime import date
from pathlib import Path
import httpx
import pytest
from app.adapters.fontes import pncp as pncp_mod
from app.adapters.fontes.pncp import _parse_item, _d
from app.domain.edital import Edital, Fonte

FIX = json.loads(Path("tests/fixtures/pncp_publicacao.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _sem_pausa_real(monkeypatch):
    """A pausa entre requests (PAUSA_ENTRE_REQUESTS) e real em producao; nos
    testes com transporte falso nao ha rate-limit a evitar, so tempo
    desperdicado. Quem quiser medir a pausa faz o proprio monkeypatch."""
    monkeypatch.setattr(pncp_mod.time, "sleep", lambda s: None)


def test_parse_item_primeiro_registo():
    item = FIX["data"][0]
    e = _parse_item(item)
    assert isinstance(e, Edital)
    assert e.fonte == Fonte.PNCP
    assert e.orgao_cnpj and e.chave_natural.count("-") == 2
    assert e.objeto  # objeto não vazio


def test_d_com_data_invalida_nao_levanta():
    assert _d("isto-nao-e-uma-data") is None
    assert _d(None) is None
    assert _d("") is None


def _client_falso(handler):
    def fake_make_client(base_url, timeout=30.0):
        return httpx.Client(base_url=base_url, transport=httpx.MockTransport(handler))
    return fake_make_client


def test_buscar_pula_item_malformado_mas_mantem_os_validos(monkeypatch):
    valido = FIX["data"][0]
    malformado = {**valido, "valorTotalEstimado": "nao-e-numero"}  # Decimal() vai levantar

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [valido, malformado], "totalPaginas": 1})

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    out = fonte.buscar(date(2026, 9, 1), date(2026, 9, 2))
    # cada modalidade devolve a mesma resposta: 1 item valido + 1 malformado descartado
    assert len(out) == len(pncp_mod.MODALIDADES)
    assert all(isinstance(e, Edital) for e in out)


def test_buscar_pula_modalidade_com_erro_mas_continua_as_outras(monkeypatch):
    valido = FIX["data"][0]
    modalidade_com_erro = pncp_mod.MODALIDADES[0]

    def handler(request: httpx.Request) -> httpx.Response:
        mod = int(request.url.params.get("codigoModalidadeContratacao"))
        if mod == modalidade_com_erro:
            return httpx.Response(400)
        return httpx.Response(200, json={"data": [valido], "totalPaginas": 1})

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    out = fonte.buscar(date(2026, 9, 1), date(2026, 9, 2))
    assert len(out) == len(pncp_mod.MODALIDADES) - 1


def test_buscar_usa_tamanho_pagina_50(monkeypatch):
    """Regressao: PNCP rejeita tamanhoPagina>50 com 400 'Tamanho de pagina invalido'."""
    vistos: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        vistos.append(int(request.url.params.get("tamanhoPagina")))
        return httpx.Response(200, json={"data": [], "totalPaginas": 1})

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    fonte.buscar(date(2025, 9, 14), date(2025, 9, 15))

    assert vistos, "nenhum request chegou a /consulta/v1/contratacoes/publicacao"
    assert all(v == 50 for v in vistos)
    assert len(vistos) == len(pncp_mod.MODALIDADES)


def test_buscar_levanta_se_todas_as_modalidades_falharem(monkeypatch):
    """Regressao: 0 sucessos nao pode devolver [] em silencio — tem de levantar."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400)

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    with pytest.raises(httpx.HTTPStatusError):
        fonte.buscar(date(2025, 9, 14), date(2025, 9, 15))


def test_parse_item_captura_situacao_compra():
    item = FIX["data"][0]
    e = _parse_item(item)
    assert e.situacao_compra == "Divulgada no PNCP"


def test_parse_item_trunca_situacao_compra_longa():
    """Regressao: situacaoCompraNome > 60 chars quebrava session.flush() (coluna
    String(60)) sem try/except ao redor, abortando a captura diaria inteira."""
    item = dict(FIX["data"][0])
    item["situacaoCompraNome"] = "x" * 80
    e = _parse_item(item)
    assert len(e.situacao_compra) == 60


def test_buscar_pausa_entre_requests(monkeypatch):
    """Regressao: rajada sem pausa disparou 429 real no PNCP (ver sessao 2026-10-08)."""
    esperas: list[float] = []
    monkeypatch.setattr(pncp_mod.time, "sleep", lambda s: esperas.append(s))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [], "totalPaginas": 1})

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    fonte.buscar(date(2026, 9, 1), date(2026, 9, 2))

    # pausa fica ANTES de cada chamada, exceto a primeira de todas - por isso
    # len(MODALIDADES)-1, nao len(MODALIDADES) (a ultima pagina nao dorme em vao).
    assert esperas == [pncp_mod.PAUSA_ENTRE_REQUESTS] * (len(pncp_mod.MODALIDADES) - 1)


def test_listar_arquivos_mapeia_tipo_por_tipo_documento_id(monkeypatch):
    resposta = [
        {"url": "http://x/1", "titulo": "Edital.zip", "tipoDocumentoId": 2, "tipoDocumentoNome": "Edital"},
        {"url": "http://x/2", "titulo": "TR.pdf", "tipoDocumentoId": 4, "tipoDocumentoNome": "Termo de Referência"},
        {"url": "http://x/3", "titulo": "ETP.pdf", "tipoDocumentoId": 7, "tipoDocumentoNome": "Estudo Técnico Preliminar"},
        {"url": "http://x/4", "titulo": "PB.pdf", "tipoDocumentoId": 6, "tipoDocumentoNome": "Projeto Básico"},
        {"url": "http://x/5", "titulo": "DFD.pdf", "tipoDocumentoId": 10, "tipoDocumentoNome": "DFD"},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=resposta)

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    e = Edital(fonte=Fonte.PNCP, chave_natural="123-2026-1", objeto="", orgao_nome="", orgao_cnpj="123",
               uf=None, municipio=None, modalidade=None, valor_estimado=None,
               data_publicacao=None, data_abertura=None, data_fim_propostas=None, url_origem="")
    arquivos = fonte.listar_arquivos(e)

    assert [a.tipo for a in arquivos] == [
        pncp_mod.TipoArquivo.EDITAL, pncp_mod.TipoArquivo.TR,
        pncp_mod.TipoArquivo.ETP, pncp_mod.TipoArquivo.PB, pncp_mod.TipoArquivo.OUTRO,
    ]


def test_listar_arquivos_nao_marca_tudo_como_edital(monkeypatch):
    """Regressao: antes desta correcao, todo arquivo virava TipoArquivo.EDITAL."""
    resposta = [{"url": "http://x/1", "titulo": "TR.pdf", "tipoDocumentoId": 4, "tipoDocumentoNome": "Termo de Referência"}]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=resposta)

    monkeypatch.setattr(pncp_mod, "make_client", _client_falso(handler))
    fonte = pncp_mod.FontePncp("http://fake")
    e = Edital(fonte=Fonte.PNCP, chave_natural="123-2026-1", objeto="", orgao_nome="", orgao_cnpj="123",
               uf=None, municipio=None, modalidade=None, valor_estimado=None,
               data_publicacao=None, data_abertura=None, data_fim_propostas=None, url_origem="")
    arquivos = fonte.listar_arquivos(e)

    assert arquivos[0].tipo != pncp_mod.TipoArquivo.EDITAL
    assert arquivos[0].tipo == pncp_mod.TipoArquivo.TR
