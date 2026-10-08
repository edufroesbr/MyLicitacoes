import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal


def _seed(objeto, uf="AM", score=0.9, status="novo", chave="k1",
          data_abertura=None, data_fim_propostas=None):
    from app.db.engine import make_session
    from app.db.models import EditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        s.add(EditalRow(fonte="pncp", chave_natural=chave, hash_conteudo="h", objeto=objeto,
                        orgao_nome="Org", orgao_cnpj="0", uf=uf, modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        data_abertura=data_abertura, data_fim_propostas=data_fim_propostas,
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


def test_paginacao_invalida_devolve_422():
    from app.api.main import app
    c = TestClient(app)
    assert c.get("/editais", params={"pagina": 0}).status_code == 422
    assert c.get("/editais", params={"pagina": -1}).status_code == 422
    assert c.get("/editais", params={"tamanho": -5}).status_code == 422


def test_busca_ignora_acento():
    _seed("Registro de preços para AQUISIÇÃO de materiais de expediente", uf="MG", chave="acento1")
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/editais", params={"q": "aquisicao"})
    assert r.status_code == 200
    assert any("AQUISIÇÃO" in e["objeto"] for e in r.json()["itens"])


def test_filtro_fase_proposta():
    hoje = date.today()
    _seed("em recebimento de propostas", chave="fase-recebendo",
          data_abertura=hoje - timedelta(days=1), data_fim_propostas=hoje + timedelta(days=5))
    _seed("propostas encerradas", chave="fase-encerrada",
          data_abertura=hoje - timedelta(days=10), data_fim_propostas=hoje - timedelta(days=1))
    _seed("ainda nao abriu", chave="fase-a-receber",
          data_abertura=hoje + timedelta(days=3), data_fim_propostas=hoje + timedelta(days=10))
    from app.api.main import app
    c = TestClient(app)

    r = c.get("/editais", params={"fase_proposta": "recebendo"})
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert "em recebimento de propostas" in objs
    assert "propostas encerradas" not in objs
    assert "ainda nao abriu" not in objs

    r = c.get("/editais", params={"fase_proposta": "encerrada"})
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert "propostas encerradas" in objs
    assert "em recebimento de propostas" not in objs

    r = c.get("/editais", params={"fase_proposta": "a_receber"})
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert "ainda nao abriu" in objs
    assert "em recebimento de propostas" not in objs


def test_fase_proposta_recebendo_nao_prende_edital_sem_nenhuma_data():
    """Regressao: edital sem data_abertura NEM data_fim_propostas (comum em
    Dispensa) caia sempre em 'recebendo' (coalesce(..., True) nos dois lados),
    e nunca em a_receber/encerrada - ficava marcado como ativo para sempre."""
    _seed("dispensa sem datas conhecidas", chave="sem-data",
          data_abertura=None, data_fim_propostas=None)
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/editais", params={"fase_proposta": "recebendo"})
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert "dispensa sem datas conhecidas" not in objs


def test_busca_escapa_wildcards_do_like():
    """Regressao: busca por 'SRP_2026' casava com 'SRPX2026' porque o _ do
    LIKE nao era escapado."""
    _seed("Pregao SRP_2026 para aquisicao", chave="srp-literal")
    _seed("Pregao SRPX2026 nao relacionado", chave="srp-wildcard")
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/editais", params={"q": "SRP_2026"})
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert "Pregao SRP_2026 para aquisicao" in objs
    assert "Pregao SRPX2026 nao relacionado" not in objs
