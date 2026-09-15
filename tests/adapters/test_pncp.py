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
