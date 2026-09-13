import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def _seed_um(chave="det1"):
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from app.db.engine import make_session
    from app.db.models import EditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        row = EditalRow(fonte="pncp", chave_natural=chave, hash_conteudo="h", objeto="clipping",
                        orgao_nome="Org", orgao_cnpj="0", uf="AM", modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        score_relevancia=0.9, status="novo", url_origem="x",
                        capturado_em=datetime.now(timezone.utc))
        s.add(row); s.commit(); return row.id


def test_detalhe_e_patch_status():
    eid = _seed_um()
    from app.api.main import app
    c = TestClient(app)
    assert c.get(f"/editais/{eid}").status_code == 200
    assert c.get("/editais/99999999").status_code == 404
    r = c.patch(f"/editais/{eid}", json={"status": "oportunidade"})
    assert r.status_code == 200 and r.json()["status"] == "oportunidade"
    assert c.patch(f"/editais/{eid}", json={"status": "xpto"}).status_code == 422
