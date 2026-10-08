import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def test_get_cria_perfil_default_na_primeira_chamada():
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/perfil")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 1
    assert body["receber_email"] is False
    assert body["receber_telegram"] is False


def test_put_persiste_e_get_seguinte_reflete_os_novos_valores():
    from app.api.main import app
    c = TestClient(app)
    novo = {"nome": "Eduardo", "email_digest": "eu@exemplo.com",
            "telegram_chat_id": "123456", "receber_email": True, "receber_telegram": True}
    r = c.put("/perfil", json=novo)
    assert r.status_code == 200
    assert r.json()["nome"] == "Eduardo"
    assert r.json()["receber_email"] is True

    r2 = c.get("/perfil")
    body = r2.json()
    assert body["nome"] == "Eduardo"
    assert body["email_digest"] == "eu@exemplo.com"
    assert body["telegram_chat_id"] == "123456"
    assert body["receber_email"] is True
    assert body["receber_telegram"] is True
