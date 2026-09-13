from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.api.deps import get_session
from app.api.schemas import EditalResumo
from app.config import Settings
from app.db.models import EditalRow, DigestLogRow

router = APIRouter()


@router.get("/digest/hoje")
def digest_hoje(session=Depends(get_session)):
    hoje = date.today()
    log = session.scalar(select(DigestLogRow).where(DigestLogRow.data_ref == hoje)
                         .order_by(DigestLogRow.enviado_em.desc()).limit(1))
    piso = Settings().score_piso
    rows = session.scalars(select(EditalRow).where(
        EditalRow.data_publicacao == hoje, EditalRow.score_relevancia >= piso)
        .order_by(EditalRow.score_relevancia.desc()).limit(20)).all()
    return {"data_ref": hoje.isoformat(),
            "resumo": (log.resumo if log else {}),
            "destaques": [EditalResumo.model_validate(r).model_dump(mode="json") for r in rows]}
