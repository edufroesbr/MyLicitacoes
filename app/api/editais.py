from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from app.api.deps import get_session
from app.api.schemas import EditalResumo, Pagina, EditalDetalhe, ArquivoResumo, MudarStatus
from app.config import Settings
from app.db.models import EditalRow, ArquivoEditalRow

router = APIRouter()


@router.get("/editais", response_model=Pagina)
def listar(session=Depends(get_session), uf: str | None = None, modalidade: str | None = None,
           fonte: str | None = None, status: str | None = None, score_min: float = 0.0,
           q: str | None = None, projeto_id: int | None = None,
           pagina: int = Query(1, ge=1), tamanho: int = Query(50, ge=1, le=200)):
    cond = [EditalRow.score_relevancia >= score_min]
    if uf: cond.append(EditalRow.uf == uf)
    if modalidade: cond.append(EditalRow.modalidade == modalidade)
    if fonte: cond.append(EditalRow.fonte == fonte)
    if status: cond.append(EditalRow.status == status)
    if q: cond.append(EditalRow.objeto.ilike(f"%{q}%"))
    if projeto_id is not None:
        from sqlalchemy import or_
        from app.db.models import ProjetoInteresseRow
        proj = session.get(ProjetoInteresseRow, projeto_id)
        if proj is not None:
            if proj.palavras_chave:
                cond.append(or_(*(EditalRow.objeto.ilike(f"%{p}%") for p in proj.palavras_chave)))
            f = proj.filtros or {}
            if f.get("uf"): cond.append(EditalRow.uf == f["uf"])
            if f.get("modalidade"): cond.append(EditalRow.modalidade == f["modalidade"])
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


@router.get("/editais/{edital_id}/arquivo/{arquivo_id}")
def servir_arquivo(edital_id: int, arquivo_id: int, session=Depends(get_session)):
    a = session.get(ArquivoEditalRow, arquivo_id)
    if a is None or a.edital_id != edital_id:
        raise HTTPException(404, "arquivo nao encontrado")
    base = Path(Settings().pdf_dir).resolve()
    caminho = Path(a.caminho_local).resolve()
    if base not in caminho.parents or not caminho.is_file():
        raise HTTPException(404, "arquivo indisponivel")
    return FileResponse(caminho, media_type="application/pdf", filename=caminho.name)
