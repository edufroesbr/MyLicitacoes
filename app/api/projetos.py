from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from app.api.deps import get_session
from app.api.schemas import ProjetoIn, ProjetoOut, ResumoProjeto, ResumoUf
from app.api._filtros_projeto import condicoes_projeto
from app.db.models import ContratoRow, EditalRow, ProjetoInteresseRow

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


@router.get("/projetos-interesse/{pid}/resumo", response_model=ResumoProjeto)
def resumo(pid: int, session=Depends(get_session)):
    proj = session.get(ProjetoInteresseRow, pid)
    if proj is None or not proj.ativo:
        raise HTTPException(404, "projeto nao encontrado")
    cond = condicoes_projeto(proj)
    hoje = date.today()
    editais_ativos = session.scalar(select(func.count()).select_from(EditalRow).where(
        *cond, func.coalesce(EditalRow.data_fim_propostas >= hoje, True))) or 0
    editais_encerrados = session.scalar(select(func.count()).select_from(EditalRow).where(
        *cond, EditalRow.data_fim_propostas < hoje)) or 0

    base = (select(ContratoRow.valor_global, EditalRow.uf)
            .join(EditalRow, ContratoRow.edital_id == EditalRow.id)
            .where(*cond)).subquery()
    contratos_quantidade = session.scalar(select(func.count()).select_from(base)) or 0
    contratos_valor_total = session.scalar(select(func.coalesce(func.sum(base.c.valor_global), 0)))
    contratos_valor_medio = session.scalar(select(func.round(func.avg(base.c.valor_global), 2)))
    por_uf = [ResumoUf(uf=uf, quantidade=qtd, valor_total=total or 0)
              for uf, qtd, total in session.execute(
                  select(base.c.uf, func.count(), func.coalesce(func.sum(base.c.valor_global), 0))
                  .group_by(base.c.uf)).all()]

    return ResumoProjeto(editais_ativos=editais_ativos, editais_encerrados=editais_encerrados,
                          contratos_quantidade=contratos_quantidade,
                          contratos_valor_total=contratos_valor_total or 0,
                          contratos_valor_medio=contratos_valor_medio, por_uf=por_uf)
