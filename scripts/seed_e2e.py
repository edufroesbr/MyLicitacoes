from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from app.config import Settings
from app.db.engine import make_session
from app.db.models import EditalRow

S = make_session(Settings().database_url)
with S() as s:
    if s.scalar(select(EditalRow).where(EditalRow.chave_natural == "e2e-seed")) is None:
        s.add(EditalRow(fonte="pncp", chave_natural="e2e-seed", hash_conteudo="h",
            objeto="Servico de clipping e monitoramento de publicacoes", orgao_nome="Tribunal X",
            orgao_cnpj="0", uf="AM", modalidade="Pregao", valor_estimado=Decimal("1000"),
            data_publicacao=date.today(), score_relevancia=0.9, motivo_relevancia="clipping",
            status="novo", url_origem="https://pncp.gov.br/x", capturado_em=datetime.now(timezone.utc)))
        s.commit()
print("seed OK")
