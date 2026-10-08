from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, or_
from app.api.deps import get_session
from app.api.schemas import EditalResumo, Pagina, EditalDetalhe, ArquivoResumo, MudarStatus
from app.config import Settings
from app.db.models import EditalRow, ArquivoEditalRow

router = APIRouter()


def _sem_acento(col):
    """ILIKE acento-insensitivo via extensao `unaccent` do Postgres (migracao
    unaccent_extension). A classificacao de relevancia ja ignora acento
    (app/domain/relevancia.py::_norm) usando uma normalizacao Python separada
    (unicodedata); as duas podem, em teoria, discordar num caractere Unicode
    raro - sao motores diferentes, nao ha um unico ponto de verdade."""
    return func.unaccent(col)


def _escapar_like(s: str) -> str:
    """Escapa os wildcards do LIKE/ILIKE (% e _) para que busca literal nao
    vire wildcard acidental (ex.: busca por "SRP_2026" nao deve casar com
    "SRPX2026"). Usar sempre junto com `.ilike(..., escape="\\\\")`."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/editais", response_model=Pagina)
def listar(session=Depends(get_session), uf: str | None = None, modalidade: str | None = None,
           fonte: str | None = None, status: str | None = None, score_min: float = 0.0,
           q: str | None = None, projeto_id: int | None = None,
           fase_proposta: str | None = None,
           pagina: int = Query(1, ge=1), tamanho: int = Query(50, ge=1, le=200)):
    cond = [EditalRow.score_relevancia >= score_min]
    if uf: cond.append(EditalRow.uf == uf)
    if modalidade: cond.append(EditalRow.modalidade == modalidade)
    if fonte: cond.append(EditalRow.fonte == fonte)
    if status: cond.append(EditalRow.status == status)
    if q: cond.append(_sem_acento(EditalRow.objeto).ilike(_sem_acento(f"%{_escapar_like(q)}%"), escape="\\"))
    if fase_proposta:
        hoje = date.today()
        if fase_proposta == "a_receber":
            cond.append(EditalRow.data_abertura > hoje)
        elif fase_proposta == "recebendo":
            # pelo menos uma data conhecida - senao um edital sem nenhuma das
            # duas datas (comum em Dispensa) cairia aqui para sempre, porque o
            # coalesce(..., True) abaixo tambem o excluiria de a_receber/encerrada.
            cond.append(or_(EditalRow.data_abertura.isnot(None), EditalRow.data_fim_propostas.isnot(None)))
            cond.append(func.coalesce(EditalRow.data_abertura <= hoje, True))
            cond.append(func.coalesce(EditalRow.data_fim_propostas >= hoje, True))
        elif fase_proposta == "encerrada":
            cond.append(EditalRow.data_fim_propostas < hoje)
    if projeto_id is not None:
        from app.db.models import ProjetoInteresseRow
        proj = session.get(ProjetoInteresseRow, projeto_id)
        if proj is None or not proj.ativo:
            raise HTTPException(404, "projeto nao encontrado")
        if proj.palavras_chave:
            cond.append(or_(*(_sem_acento(EditalRow.objeto).ilike(_sem_acento(f"%{_escapar_like(p)}%"), escape="\\")
                               for p in proj.palavras_chave)))
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
