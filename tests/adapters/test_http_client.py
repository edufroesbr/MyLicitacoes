# tests/adapters/test_http_client.py
import httpx
from app.adapters.http_client import make_client


def test_make_client_config():
    c = make_client("https://example.test")
    assert isinstance(c, httpx.Client)
    assert str(c.base_url).startswith("https://example.test")
    c.close()
