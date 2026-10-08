# app/adapters/http_client.py
import ssl
import time
import certifi
import httpx


class _RetryTransitorio(httpx.BaseTransport):
    """Re-tenta respostas transitorias: 5xx e 429 (o retry nativo do httpx so
    cobre falhas de conexao/timeout, nao status HTTP). O PNCP devolve 500
    intermitente na mesma query valida, e rate-limita com 429 sob volume
    moderado de pedidos — sem isto a captura desiste ou aborta a fonte.
    No 429, honra o header Retry-After quando presente; sem ele, cai no
    mesmo backoff linear fixo do 5xx."""

    def __init__(self, inner: httpx.BaseTransport, tentativas: int = 4, espera: float = 2.0) -> None:
        self._inner = inner
        self._tentativas = tentativas
        self._espera = espera

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        for i in range(self._tentativas):
            resp = self._inner.handle_request(request)
            transitorio = resp.status_code >= 500 or resp.status_code == 429
            if not transitorio or i == self._tentativas - 1:
                return resp
            resp.read()  # consumir o corpo antes de re-tentar
            resp.close()
            espera = self._espera * (i + 1)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        espera = float(retry_after)
                    except ValueError:
                        pass
            if espera:
                time.sleep(espera)
        return resp  # inalcancavel (o loop devolve sempre), mas satisfaz o tipo

    def close(self) -> None:
        self._inner.close()


def make_client(base_url: str, timeout: float = 90.0, retry_espera: float = 2.0) -> httpx.Client:  # PNCP e lento/instavel
    ctx = ssl.create_default_context(cafile=certifi.where())
    transport = _RetryTransitorio(httpx.HTTPTransport(retries=3, verify=ctx), espera=retry_espera)
    return httpx.Client(base_url=base_url, timeout=timeout,
                        follow_redirects=True, transport=transport,
                        headers={"User-Agent": "MyLicitacoes/0.1 (radar de editais)"})
