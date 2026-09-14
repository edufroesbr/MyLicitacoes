# app/adapters/http_client.py
import ssl
import certifi
import httpx


def make_client(base_url: str, timeout: float = 30.0) -> httpx.Client:
    ctx = ssl.create_default_context(cafile=certifi.where())
    transport = httpx.HTTPTransport(retries=3, verify=ctx)
    return httpx.Client(base_url=base_url, timeout=timeout,
                        follow_redirects=True, transport=transport,
                        headers={"User-Agent": "MyLicitacoes/0.1 (radar de editais)"})
