import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def test_serve_pdf_do_disco(tmp_path, monkeypatch):
    monkeypatch.setenv("MYLIC_PDF_DIR", str(tmp_path))
    pdf = tmp_path / "e.pdf"; pdf.write_bytes(b"%PDF-1.4 x")
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from app.db.engine import make_session
    from app.db.models import EditalRow, ArquivoEditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        row = EditalRow(fonte="pncp", chave_natural="arq1", hash_conteudo="h", objeto="clipping",
                        orgao_nome="Org", orgao_cnpj="0", uf="AM", modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        score_relevancia=0.9, status="novo", url_origem="x",
                        capturado_em=datetime.now(timezone.utc))
        s.add(row); s.flush()
        a = ArquivoEditalRow(edital_id=row.id, tipo="edital", caminho_local=str(pdf),
                             hash="h", baixado_em=datetime.now(timezone.utc))
        s.add(a); s.commit(); eid, aid = row.id, a.id
    from app.api.main import app
    c = TestClient(app)
    r = c.get(f"/editais/{eid}/arquivo/{aid}")
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert c.get(f"/editais/{eid}/arquivo/99999").status_code == 404
