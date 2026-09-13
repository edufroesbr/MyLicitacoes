from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from app.api.deps import get_session
from app.api.schemas import EditalResumo, Pagina, EditalDetalhe, ArquivoResumo, MudarStatus
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


@router.get("/editais/{edital_id}", response_model=EditalDetalhe)
def detalhe(edital_id: int, session=Depends(get_session)):
    row = session.get(EditalRow, edital_id)
    if row is None:
        raise HTTPException(404, "edital nao encontrado")
    return _detalhe(row)


@router.patch("/editais/{edital_id}", response_model=EditalDetalhe)
def mudar_status(edital_id: int, body: MudarStatus, session=Depends(get_session)):
    row = session.get(EditalRow, edital_id)
    if row is None:
        raise HTTPException(404, "edital nao encontrado")
    row.status = body.status.value
    session.commit()
    return _detalhe(row)


def _detalhe(row):
    d = EditalDetalhe.model_validate(row)
    d.arquivos = [ArquivoResumo.model_validate(a) for a in row.arquivos]
    return d
