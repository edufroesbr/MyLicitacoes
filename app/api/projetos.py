from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from app.api.deps import get_session
from app.api.schemas import ProjetoIn, ProjetoOut
from app.db.models import ProjetoInteresseRow

router = APIRouter()


@router.get("/projetos-interesse", response_model=list[ProjetoOut])
def listar(session=Depends(get_session)):
    return session.scalars(select(ProjetoInteresseRow)).all()


@router.post("/projetos-interesse", response_model=ProjetoOut, status_code=201)
def criar(body: ProjetoIn, session=Depends(get_session)):
    row = ProjetoInteresseRow(nome=body.nome, palavras_chave=body.palavras_chave,
                              filtros=body.filtros, ativo=body.ativo,
                              criado_em=datetime.now(timezone.utc))
    session.add(row); session.commit()
    return row


@router.put("/projetos-interesse/{pid}", response_model=ProjetoOut)
def atualizar(pid: int, body: ProjetoIn, session=Depends(get_session)):
    row = session.get(ProjetoInteresseRow, pid)
    if row is None:
        raise HTTPException(404, "projeto nao encontrado")
    row.nome, row.palavras_chave, row.filtros, row.ativo = body.nome, body.palavras_chave, body.filtros, body.ativo
    session.commit()
    return row


@router.delete("/projetos-interesse/{pid}", status_code=204)
def apagar(pid: int, session=Depends(get_session)):
    row = session.get(ProjetoInteresseRow, pid)
    if row is not None:
        session.delete(row); session.commit()
    return Response(status_code=204)
