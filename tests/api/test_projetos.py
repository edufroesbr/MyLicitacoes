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


def _seed_edital(chave, dias_fim_propostas, objeto="clipping resumo"):
    from datetime import date, datetime, timedelta, timezone
    from decimal import Decimal
    from app.db.engine import make_session
    from app.db.models import EditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        row = EditalRow(fonte="pncp", chave_natural=chave, hash_conteudo="h", objeto=objeto,
                        orgao_nome="Org", orgao_cnpj="0", uf="AM", modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        data_fim_propostas=date.today() + timedelta(days=dias_fim_propostas),
                        score_relevancia=0.9, status="novo", url_origem="x",
                        capturado_em=datetime.now(timezone.utc))
        s.add(row); s.commit(); return row.id


def test_resumo_projeto():
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from app.db.engine import make_session
    from app.db.models import ContratoRow

    from app.api.main import app
    c = TestClient(app)
    pid = c.post("/projetos-interesse", json={"nome": "Resumo Teste",
                 "palavras_chave": ["clipping-resumo-teste"], "filtros": {}}).json()["id"]

    eid_ativo = _seed_edital("resumo-ativo", dias_fim_propostas=10, objeto="clipping-resumo-teste A")
    eid_encerrado = _seed_edital("resumo-encerrado", dias_fim_propostas=-10, objeto="clipping-resumo-teste B")

    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        s.add(ContratoRow(fonte="pncp", chave_natural="c-resumo-1", edital_id=eid_ativo,
                          numero_contrato="1/2026", fornecedor_nome="Forn", fornecedor_documento="0",
                          valor_global=Decimal("200.00"), data_assinatura=date(2026, 1, 1),
                          capturado_em=datetime.now(timezone.utc)))
        s.commit()

    r = c.get(f"/projetos-interesse/{pid}/resumo")
    assert r.status_code == 200
    body = r.json()
    assert body["editais_ativos"] == 1
    assert body["editais_encerrados"] == 1
    assert body["contratos_quantidade"] == 1
    assert body["contratos_valor_total"] == "200.00"
    assert Decimal(body["contratos_valor_medio"]) == Decimal("200.00")
    assert body["por_uf"] == [{"uf": "AM", "quantidade": 1, "valor_total": "200.00"}]


def test_resumo_projeto_inexistente_404():
    from app.api.main import app
    c = TestClient(app)
    assert c.get("/projetos-interesse/999999/resumo").status_code == 404


def test_resumo_projeto_inativo_404():
    from app.api.main import app
    c = TestClient(app)
    pid = c.post("/projetos-interesse", json={"nome": "Resumo Inativo",
                 "palavras_chave": [], "filtros": {}}).json()["id"]
    assert c.put(f"/projetos-interesse/{pid}", json={"nome": "Resumo Inativo",
                 "palavras_chave": [], "filtros": {}, "ativo": False}).status_code == 200
    assert c.get(f"/projetos-interesse/{pid}/resumo").status_code == 404
