import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def test_crud_projeto_e_filtro():
    from app.api.main import app
    c = TestClient(app)
    r = c.post("/projetos-interesse", json={"nome": "DJE Nordeste",
              "palavras_chave": ["dje", "clipping"], "filtros": {"uf": "AM"}})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert any(p["id"] == pid for p in c.get("/projetos-interesse").json())
    assert c.put(f"/projetos-interesse/{pid}", json={"nome": "DJE NE", "palavras_chave": ["dje"],
                 "filtros": {}, "ativo": False}).status_code == 200
    assert c.get("/editais", params={"projeto_id": pid}).status_code == 404
    assert c.delete(f"/projetos-interesse/{pid}").status_code == 204


def test_projeto_id_inexistente_404():
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/editais", params={"projeto_id": 999999})
    assert r.status_code == 404
