# app/adapters/http_client.py
import ssl
import time
import certifi
import httpx


class _Retry5xx(httpx.BaseTransport):
    """Re-tenta respostas 5xx (o retry nativo do httpx so cobre falhas de
    conexao/timeout, nao status HTTP). O PNCP devolve 500 intermitente na mesma
    query valida; sem isto a captura desiste.
    ponytail: backoff linear fixo; exponencial+jitter se a carga justificar."""

    def __init__(self, inner: httpx.BaseTransport, tentativas: int = 4, espera: float = 2.0) -> None:
        self._inner = inner
        self._tentativas = tentativas
        self._espera = espera

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        for i in range(self._tentativas):
            resp = self._inner.handle_request(request)
            if resp.status_code < 500 or i == self._tentativas - 1:
                return resp
            resp.read()  # consumir o corpo do 5xx antes de re-tentar
            resp.close()
            if self._espera:
                time.sleep(self._espera * (i + 1))
        return resp  # inalcancavel (o loop devolve sempre), mas satisfaz o tipo

    def close(self) -> None:
        self._inner.close()


def make_client(base_url: str, timeout: float = 90.0, retry_espera: float = 2.0) -> httpx.Client:  # PNCP e lento/instavel
    ctx = ssl.create_default_context(cafile=certifi.where())
    transport = _Retry5xx(httpx.HTTPTransport(retries=3, verify=ctx), espera=retry_espera)
    return httpx.Client(base_url=base_url, timeout=timeout,
                        follow_redirects=True, transport=transport,
                        headers={"User-Agent": "MyLicitacoes/0.1 (radar de editais)"})
