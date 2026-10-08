import pytest
import httpx
from app.adapters.http_client import _RetryTransitorio, ESPERA_MAXIMA


def test_retry_re_tenta_5xx_e_devolve_200():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        return httpx.Response(500 if chamadas["n"] < 3 else 200, text="ok")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=4, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 200
    assert chamadas["n"] == 3  # 2 falhas + 1 sucesso


def test_retry_desiste_apos_tentativas_devolve_ultimo_5xx():
    def handler(request):
        return httpx.Response(500, text="fail")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=3, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 500


def test_retry_nao_re_tenta_4xx_comum():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        return httpx.Response(400, text="bad")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=4, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 400
    assert chamadas["n"] == 1  # 4xx comum nao re-tenta


def test_retry_429_re_tenta_e_devolve_200():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        return httpx.Response(429 if chamadas["n"] < 3 else 200, text="ok")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=4, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 200
    assert chamadas["n"] == 3


def test_retry_429_sem_retry_after_usa_backoff(monkeypatch):
    esperas: list[float] = []
    monkeypatch.setattr("app.adapters.http_client.time.sleep", lambda s: esperas.append(s))

    def handler(request):
        return httpx.Response(429, text="slow down")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=3, espera=2.0)
    t.handle_request(httpx.Request("GET", "http://x/y"))
    assert esperas == [2.0, 4.0]  # backoff linear, igual ao 5xx


def test_retry_429_respeita_retry_after_header(monkeypatch):
    esperas: list[float] = []
    monkeypatch.setattr("app.adapters.http_client.time.sleep", lambda s: esperas.append(s))

    def handler(request):
        return httpx.Response(429, headers={"Retry-After": "7"}, text="slow down")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=2, espera=2.0)
    t.handle_request(httpx.Request("GET", "http://x/y"))
    assert esperas == [7.0]  # ignora o backoff fixo, usa o header


def test_retry_429_retry_after_negativo_ou_inf_cai_no_backoff(monkeypatch):
    """Regressao: float('-5') e float('inf') nao levantam ValueError, escapavam
    do except e estouravam em time.sleep (ValueError/OverflowError nao tratados)."""
    esperas: list[float] = []
    monkeypatch.setattr("app.adapters.http_client.time.sleep", lambda s: esperas.append(s))

    def handler_negativo(request):
        return httpx.Response(429, headers={"Retry-After": "-5"}, text="x")

    t = _RetryTransitorio(httpx.MockTransport(handler_negativo), tentativas=2, espera=2.0)
    t.handle_request(httpx.Request("GET", "http://x/y"))
    assert esperas == [2.0]  # ignora o valor patologico, usa o backoff

    esperas.clear()

    def handler_inf(request):
        return httpx.Response(429, headers={"Retry-After": "inf"}, text="x")

    t2 = _RetryTransitorio(httpx.MockTransport(handler_inf), tentativas=2, espera=2.0)
    t2.handle_request(httpx.Request("GET", "http://x/y"))
    assert esperas == [2.0]


def test_retry_429_retry_after_http_date_e_reconhecido(monkeypatch):
    """Regressao: Retry-After em formato HTTP-date (RFC 7231) caia no except
    e usava o backoff fixo em silencio, contradizendo o docstring da classe."""
    from datetime import datetime, timedelta, timezone
    from email.utils import format_datetime
    import app.adapters.http_client as hc

    agora = datetime(2026, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(hc, "datetime", type("D", (), {"now": staticmethod(lambda tz=None: agora)}))
    esperas: list[float] = []
    monkeypatch.setattr(hc.time, "sleep", lambda s: esperas.append(s))
    alvo = format_datetime(agora + timedelta(seconds=30))

    def handler(request):
        return httpx.Response(429, headers={"Retry-After": alvo}, text="x")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=2, espera=2.0)
    t.handle_request(httpx.Request("GET", "http://x/y"))
    assert esperas == [30.0]


def test_retry_429_retry_after_e_limitado_a_espera_maxima(monkeypatch):
    """Regressao: Retry-After valido mas enorme (ex.: 3600s) bloqueava a
    thread por horas, sem limite superior ligado ao timeout do client."""
    esperas: list[float] = []
    monkeypatch.setattr("app.adapters.http_client.time.sleep", lambda s: esperas.append(s))

    def handler(request):
        return httpx.Response(429, headers={"Retry-After": "3600"}, text="x")

    t = _RetryTransitorio(httpx.MockTransport(handler), tentativas=2, espera=2.0)
    t.handle_request(httpx.Request("GET", "http://x/y"))
    assert esperas == [ESPERA_MAXIMA]


def test_retry_transitorio_rejeita_tentativas_invalidas():
    """Regressao: tentativas<=0 levantava UnboundLocalError (resp nunca
    atribuido) em vez de um erro de validacao claro."""
    with pytest.raises(ValueError):
        _RetryTransitorio(httpx.MockTransport(lambda r: httpx.Response(200)), tentativas=0)
