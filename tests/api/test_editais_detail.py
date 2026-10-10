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


def test_detalhe_busca_catalogo_ao_vivo_quando_sem_arquivo_local(monkeypatch):
    """Regressao: edital fora do piso de relevancia nunca tem arquivo
    baixado automaticamente, mas o catalogo na fonte existe de verdade -
    o detalhe deve busca-lo ao vivo em vez de so mostrar 'nenhum arquivo'."""
    from app.domain.edital import ArquivoRef, TipoArquivo
    import app.api.editais as editais_mod

    monkeypatch.setattr(editais_mod.FontePncp, "listar_arquivos", lambda self, e: [
        ArquivoRef(TipoArquivo.EDITAL, "http://pncp.fake/e.pdf", "Edital.pdf"),
    ])
    eid = _seed_um("det-catalogo-1")
    from app.api.main import app
    c = TestClient(app)
    r = c.get(f"/editais/{eid}")
    assert r.status_code == 200
    assert r.json()["arquivos"] == []
    assert r.json()["arquivos_catalogo"] == [
        {"tipo": "edital", "nome": "Edital.pdf", "url": "http://pncp.fake/e.pdf"}
    ]


def test_detalhe_nao_quebra_se_fonte_estiver_fora_do_ar(monkeypatch):
    import app.api.editais as editais_mod

    def explode(self, e):
        raise RuntimeError("pncp fora do ar")
    monkeypatch.setattr(editais_mod.FontePncp, "listar_arquivos", explode)
    eid = _seed_um("det-catalogo-2")
    from app.api.main import app
    c = TestClient(app)
    r = c.get(f"/editais/{eid}")
    assert r.status_code == 200
    assert r.json()["arquivos_catalogo"] == []
