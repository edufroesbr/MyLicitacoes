import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def test_digest_hoje_devolve_estrutura():
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/digest/hoje")
    assert r.status_code == 200
    body = r.json()
    assert "data_ref" in body and "resumo" in body and "destaques" in body
