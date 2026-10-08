import httpx
from app.adapters.http_client import _RetryTransitorio


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
