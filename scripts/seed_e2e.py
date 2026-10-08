from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from sqlalchemy import select
from app.config import Settings
from app.db.engine import make_session
from app.db.models import ArquivoEditalRow, EditalRow

PDF_MINIMO = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 72 72]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF"
)

settings = Settings()
S = make_session(settings.database_url)
with S() as s:
    edital = s.scalar(select(EditalRow).where(EditalRow.chave_natural == "e2e-seed"))
    if edital is None:
        edital = EditalRow(fonte="pncp", chave_natural="e2e-seed", hash_conteudo="h",
            objeto="Servico de clipping e monitoramento de publicacoes", orgao_nome="Tribunal X",
            orgao_cnpj="0", uf="AM", modalidade="Pregao", valor_estimado=Decimal("1000"),
            data_publicacao=date.today(), score_relevancia=0.9, motivo_relevancia="clipping",
            status="novo", url_origem="https://pncp.gov.br/x", capturado_em=datetime.now(timezone.utc))
        s.add(edital)
    else:
        edital.status = "novo"  # os specs esperam o estado canonico a cada corrida, nao o residuo da anterior
    s.commit()

    edital2 = s.scalar(select(EditalRow).where(EditalRow.chave_natural == "e2e-seed-2"))
    if edital2 is None:
        edital2 = EditalRow(fonte="compras_gov", chave_natural="e2e-seed-2", hash_conteudo="h2",
            objeto="Aquisicao de mobiliario de escritorio", orgao_nome="Prefeitura Y",
            orgao_cnpj="1", uf="SP", modalidade="Concorrencia", valor_estimado=Decimal("500"),
            data_publicacao=date.today(), score_relevancia=0.2, motivo_relevancia="",
            status="arquivado", url_origem="https://compras.gov.br/y", capturado_em=datetime.now(timezone.utc))
        s.add(edital2)
    else:
        edital2.status = "arquivado"
    s.commit()
    if s.scalar(select(ArquivoEditalRow).where(ArquivoEditalRow.edital_id == edital.id)) is None:
        pdf_dir = Path(settings.pdf_dir)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        caminho = pdf_dir / "e2e-seed.pdf"
        if not caminho.exists():
            caminho.write_bytes(PDF_MINIMO)
        s.add(ArquivoEditalRow(edital_id=edital.id, tipo="edital", caminho_local=str(caminho.resolve()),
            hash="h", baixado_em=datetime.now(timezone.utc)))
        s.commit()
print("seed OK")
