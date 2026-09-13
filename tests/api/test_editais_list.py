import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient
from datetime import date, datetime, timezone
from decimal import Decimal


def _seed(objeto, uf="AM", score=0.9, status="novo", chave="k1"):
    from app.db.engine import make_session
    from app.db.models import EditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        s.add(EditalRow(fonte="pncp", chave_natural=chave, hash_conteudo="h", objeto=objeto,
                        orgao_nome="Org", orgao_cnpj="0", uf=uf, modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        score_relevancia=score, status=status, url_origem="x",
                        capturado_em=datetime.now(timezone.utc)))
        s.commit()


def test_lista_filtra_por_uf_e_busca():
    _seed("servico de clipping", uf="AM", chave="am1")
    _seed("merenda escolar", uf="SP", chave="sp1")
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/editais", params={"uf": "AM"})
    assert r.status_code == 200
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert any("clipping" in o for o in objs) and all("merenda" not in o for o in objs)
    r2 = c.get("/editais", params={"q": "clipping"})
    assert any("clipping" in e["objeto"] for e in r2.json()["itens"])
