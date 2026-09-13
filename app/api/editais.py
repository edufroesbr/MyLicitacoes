from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from app.api.deps import get_session
from app.api.schemas import EditalResumo, Pagina
from app.db.models import EditalRow

router = APIRouter()


@router.get("/editais", response_model=Pagina)
def listar(session=Depends(get_session), uf: str | None = None, modalidade: str | None = None,
           fonte: str | None = None, status: str | None = None, score_min: float = 0.0,
           q: str | None = None, pagina: int = 1, tamanho: int = Query(50, le=200)):
    cond = [EditalRow.score_relevancia >= score_min]
    if uf: cond.append(EditalRow.uf == uf)
    if modalidade: cond.append(EditalRow.modalidade == modalidade)
    if fonte: cond.append(EditalRow.fonte == fonte)
    if status: cond.append(EditalRow.status == status)
    if q: cond.append(EditalRow.objeto.ilike(f"%{q}%"))
    total = session.scalar(select(func.count()).select_from(EditalRow).where(*cond))
    rows = session.scalars(select(EditalRow).where(*cond)
                           .order_by(EditalRow.score_relevancia.desc(), EditalRow.data_publicacao.desc())
                           .offset((pagina - 1) * tamanho).limit(tamanho)).all()
    return Pagina(itens=[EditalResumo.model_validate(r) for r in rows],
                  total=total or 0, pagina=pagina, tamanho=tamanho)
