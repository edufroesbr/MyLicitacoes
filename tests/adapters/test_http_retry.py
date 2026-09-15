import httpx
from app.adapters.http_client import _Retry5xx


def test_retry5xx_re_tenta_e_devolve_200():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        return httpx.Response(500 if chamadas["n"] < 3 else 200, text="ok")

    t = _Retry5xx(httpx.MockTransport(handler), tentativas=4, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 200
    assert chamadas["n"] == 3  # 2 falhas + 1 sucesso


def test_retry5xx_desiste_apos_tentativas_devolve_ultimo_5xx():
    def handler(request):
        return httpx.Response(500, text="fail")

    t = _Retry5xx(httpx.MockTransport(handler), tentativas=3, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 500


def test_retry5xx_nao_re_tenta_4xx():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        return httpx.Response(400, text="bad")

    t = _Retry5xx(httpx.MockTransport(handler), tentativas=4, espera=0)
    resp = t.handle_request(httpx.Request("GET", "http://x/y"))
    assert resp.status_code == 400
    assert chamadas["n"] == 1  # 4xx nao re-tenta
