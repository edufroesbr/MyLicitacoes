# Fase 1B-A — Backend gap-fix + API FastAPI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar o gap do 1A (persistir `arquivo_edital`) e expor uma API FastAPI local (sem auth) que serve a caixa Next.js: listar/filtrar/buscar editais, detalhe, mudar status, servir o PDF do disco, digest do dia, e CRUD de projetos de interesse.

**Architecture:** FastAPI sobre a mesma stack do 1A (SQLAlchemy sync + Postgres). Sem camada de auth (so localhost). A API e um adaptador de entrada; le/escreve via `app/db` e reusa o dominio. Ponytail: filtros por condicionais, busca por `ILIKE`, PDF por `FileResponse` com contencao de caminho.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, SQLAlchemy 2.0, Postgres, pytest + httpx TestClient.

**Spec:** [`docs/superpowers/specs/2026-09-10-radar-editais-lexflow-design.md`](../specs/2026-09-10-radar-editais-lexflow-design.md) §8; [`docs/prd/radar-editais-lexflow/requirements.md`](../../prd/radar-editais-lexflow/requirements.md) Fase 1.8.

## Global Constraints

- **Repo:** `C:\Users\edufr\.gemini\antigravity-ide\scratch\MyLicitacoes`, branch `feat/fase1a-agente` (ou branch nova `feat/fase1b-api` a partir dela — decisao do controlador SDD).
- Sem `requirements.txt`; deps no `pyproject.toml`, `uv sync`. `app/domain` intocado (contrato import-linter KEPT).
- **Sem auth** — a API so escuta em localhost; nao adicionar login/tokens.
- Postgres real para testes: `MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5433/mylic`, `uv run alembic upgrade head` antes.
- Windows/Git Bash; gate Fact-Forcing (fatos antes do 1.o Bash e de cada Write/Edit novo; repetir).
- TDD estrito; pt-BR na prosa, ASCII no codigo.

---

### Task 1: `upsert_editais` devolve ids + orquestrador persiste `arquivo_edital`

**Files:**
- Modify: `app/db/repo.py`, `app/scheduler/orquestrador.py`
- Test: `tests/db/test_repo.py`, `tests/scheduler/test_orquestrador.py`

**Interfaces:**
- Consumes: `Edital`, `ArquivoRef`, `EditalRow`, `ArquivoEditalRow`.
- Produces:
  - `upsert_editais(...) -> tuple[dict[tuple[str,str], int], int]` — devolve `({(fonte, chave_natural): edital_id}, novos)` para TODOS os editais processados.
  - `persistir_arquivo(session, edital_id, arq: ArquivoRef, caminho: str, conteudo: bytes) -> None` em `repo.py` — grava `ArquivoEditalRow` (tipo, caminho_local, hash=sha256, baixado_em); idempotente por `(edital_id, caminho_local)`.

- [ ] **Step 1: Write the failing test (repo, Postgres)**

```python
# tests/db/test_repo.py  (acrescentar)
def test_upsert_devolve_ids_e_persistir_arquivo():
    import os, pytest
    if not os.getenv("MYLIC_DATABASE_URL"):
        pytest.skip("sem Postgres")
    from datetime import date
    from decimal import Decimal
    from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo
    from app.domain.relevancia import ScoreRelevancia
    from app.domain.dedup import hash_conteudo
    from app.db.engine import make_session
    from app.db import repo
    from app.db.models import ArquivoEditalRow
    Session = make_session(os.environ["MYLIC_DATABASE_URL"])
    with Session() as s:
        e = Edital(Fonte.PNCP, "00000000000191-2026-99", "clipping", "Org", "00000000000191",
                   "AM", "Manaus", "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")
        ids, novos = repo.upsert_editais(s, [(e, ScoreRelevancia(0.9, ("clipping",)), hash_conteudo(e))])
        s.commit()
        eid = ids[(e.fonte.value, e.chave_natural)]
        assert isinstance(eid, int)
        arq = ArquivoRef(TipoArquivo.EDITAL, "http://x/e.pdf", "e.pdf")
        repo.persistir_arquivo(s, eid, arq, "/tmp/e.pdf", b"%PDF")
        s.commit()
        rows = s.query(ArquivoEditalRow).filter_by(edital_id=eid).all()
        assert len(rows) == 1 and rows[0].hash
```

- [ ] **Step 2: Run to verify it fails**

Run: `MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5433/mylic uv run pytest tests/db/test_repo.py -k arquivo -v`
Expected: FAIL (`upsert_editais` nao devolve dict; `persistir_arquivo` inexistente).

- [ ] **Step 3: Implement**

Em `app/db/repo.py`, `upsert_editais` passa a acumular ids (com `session.flush()` para obter o id dos novos) e devolve `(ids, novos)`:

```python
def upsert_editais(session, editais_com_score):
    ids: dict[tuple[str, str], int] = {}
    novos = 0
    for e, sc, h in editais_com_score:
        row = session.scalar(select(EditalRow).where(
            EditalRow.fonte == e.fonte.value, EditalRow.chave_natural == e.chave_natural))
        if row is None:
            row = EditalRow(
                fonte=e.fonte.value, chave_natural=e.chave_natural, hash_conteudo=h,
                objeto=e.objeto, orgao_nome=e.orgao_nome, orgao_cnpj=e.orgao_cnpj,
                uf=e.uf, municipio=e.municipio, modalidade=e.modalidade,
                valor_estimado=e.valor_estimado, data_publicacao=e.data_publicacao,
                data_abertura=e.data_abertura, data_fim_propostas=e.data_fim_propostas,
                score_relevancia=sc.valor, motivo_relevancia=",".join(sc.termos),
                status="novo", url_origem=e.url_origem, capturado_em=datetime.now(timezone.utc))
            session.add(row)
            session.flush()
            novos += 1
        elif row.hash_conteudo != h:
            row.hash_conteudo = h
            row.objeto = e.objeto
            row.score_relevancia = sc.valor
            row.motivo_relevancia = ",".join(sc.termos)
        ids[(e.fonte.value, e.chave_natural)] = row.id
    return ids, novos
```

```python
# repo.py — nova funcao
import hashlib
from app.db.models import ArquivoEditalRow

def persistir_arquivo(session, edital_id, arq, caminho, conteudo):
    ja = session.scalar(select(ArquivoEditalRow).where(
        ArquivoEditalRow.edital_id == edital_id,
        ArquivoEditalRow.caminho_local == caminho))
    if ja is not None:
        return
    session.add(ArquivoEditalRow(
        edital_id=edital_id, tipo=arq.tipo.value, caminho_local=caminho,
        hash=hashlib.sha256(conteudo).hexdigest(), baixado_em=datetime.now(timezone.utc)))
```

Em `app/scheduler/orquestrador.py`, ajusta ao novo retorno e persiste arquivos por edital (mantendo o isolamento por edital ja existente):

```python
    ids, res.novos = upsert_editais(session, com_score)
    session.commit()
    ...
    for e in relevantes:
        fonte = por_nome.get(e.fonte.value)
        if fonte is None:
            continue
        eid = ids.get((e.fonte.value, e.chave_natural))
        try:
            for arq in fonte.listar_arquivos(e):
                if not arq.url:
                    continue
                conteudo = baixar_conteudo(arq.url)
                caminho = armazenamento.guardar(e, arq, conteudo)
                if eid is not None:
                    persistir_arquivo(session, eid, arq, caminho, conteudo)
                res.downloads += 1
            session.commit()
        except Exception:
            session.rollback()
```

Importa `persistir_arquivo` no orquestrador. Atualiza `tests/scheduler/test_orquestrador.py`: o `upsert_editais` monkeypatched passa a devolver `({(f, k): 1 ...}, len(itens))`; adiciona `persistir_arquivo` ao monkeypatch como no-op.

- [ ] **Step 4: Run to verify it passes**

Run: `MYLIC_DATABASE_URL=... uv run alembic upgrade head && MYLIC_DATABASE_URL=... uv run pytest tests/db/test_repo.py tests/scheduler -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/db/repo.py app/scheduler/orquestrador.py tests/db/test_repo.py tests/scheduler/test_orquestrador.py
git commit -m "feat(agente): persistir arquivo_edital (FK+hash) ao baixar; upsert devolve ids"
```

---

### Task 2: App FastAPI + `GET /editais` (filtros + busca + paginacao)

**Files:**
- Create: `app/api/__init__.py`, `app/api/main.py`, `app/api/deps.py`, `app/api/schemas.py`, `app/api/editais.py`
- Modify: `pyproject.toml` (add `fastapi`, `uvicorn[standard]`)
- Test: `tests/api/__init__.py`, `tests/api/test_editais_list.py`

**Interfaces:**
- Produces:
  - `app/api/main.py`: `app = FastAPI()`, inclui routers.
  - `app/api/deps.py`: `get_session()` dependency (sessionmaker via `@lru_cache`).
  - `app/api/schemas.py`: `EditalResumo`, `Pagina`.
  - `GET /editais` params: `uf`, `modalidade`, `fonte`, `status`, `score_min: float=0`, `q`, `pagina:int=1`, `tamanho:int=50` (<=200). Ordena `score_relevancia desc, data_publicacao desc`. (`projeto_id` -> Task 6.)

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_editais_list.py
import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient
from datetime import date, datetime, timezone
from decimal import Decimal


def _seed(objeto, uf="AM", score=0.9, status="novo", chave="k1"):
    from app.db.engine import make_session
    from app.db.models import EditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        s.add(EditalRow(fonte="pncp", chave_natural=chave, hash_conteudo="h", objeto=objeto,
                        orgao_nome="Org", orgao_cnpj="0", uf=uf, modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        score_relevancia=score, status=status, url_origem="x",
                        capturado_em=datetime.now(timezone.utc)))
        s.commit()


def test_lista_filtra_por_uf_e_busca():
    _seed("servico de clipping", uf="AM", chave="am1")
    _seed("merenda escolar", uf="SP", chave="sp1")
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/editais", params={"uf": "AM"})
    assert r.status_code == 200
    objs = [e["objeto"] for e in r.json()["itens"]]
    assert any("clipping" in o for o in objs) and all("merenda" not in o for o in objs)
    r2 = c.get("/editais", params={"q": "clipping"})
    assert any("clipping" in e["objeto"] for e in r2.json()["itens"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `MYLIC_DATABASE_URL=... uv run pytest tests/api/test_editais_list.py -v` -> FAIL (`app.api.main` inexistente).

- [ ] **Step 3: Implement**

```python
# app/api/deps.py
from functools import lru_cache
from app.config import Settings
from app.db.engine import make_session


@lru_cache
def _sessionmaker():
    return make_session(Settings().database_url)


def get_session():
    S = _sessionmaker()
    with S() as s:
        yield s
```

```python
# app/api/schemas.py
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class EditalResumo(BaseModel):
    id: int
    fonte: str
    objeto: str
    orgao_nome: str
    uf: str | None
    modalidade: str | None
    valor_estimado: Decimal | None
    data_publicacao: date | None
    data_fim_propostas: date | None
    score_relevancia: float
    status: str
    model_config = {"from_attributes": True}


class Pagina(BaseModel):
    itens: list[EditalResumo]
    total: int
    pagina: int
    tamanho: int
```

```python
# app/api/editais.py
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
```

```python
# app/api/main.py
from fastapi import FastAPI
from app.api import editais

app = FastAPI(title="MyLicitacoes")
app.include_router(editais.router)
```

Add to `pyproject.toml` deps: `"fastapi>=0.111"`, `"uvicorn[standard]>=0.30"`. `uv sync`.
> **Ruling do implementador:** `projeto_id` fica de fora do endpoint ate a Task 6 (nao fingir um filtro inerte).

- [ ] **Step 4: Run to verify it passes**

Run: `MYLIC_DATABASE_URL=... uv run pytest tests/api/test_editais_list.py -v && uv run lint-imports` -> PASS; contrato KEPT.

- [ ] **Step 5: Commit**

```bash
git add app/api pyproject.toml uv.lock tests/api
git commit -m "feat(api): app FastAPI + GET /editais (filtros, busca ilike, paginacao)"
```

---

### Task 3: `GET /editais/{id}` (detalhe + arquivos) e `PATCH /editais/{id}` (status)

**Files:**
- Modify: `app/api/editais.py`, `app/api/schemas.py`
- Test: `tests/api/test_editais_detail.py`

**Interfaces:**
- Produces: `EditalDetalhe` (EditalResumo + orgao_cnpj, municipio, motivo_relevancia, url_origem, arquivos), `ArquivoResumo` (id, tipo), `MudarStatus` (status: StatusCaixa). `GET /editais/{id}` (404 se ausente); `PATCH /editais/{id}` body `{"status": ...}` (422 invalido).

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_editais_detail.py
import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def _seed_um(chave="det1"):
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from app.db.engine import make_session
    from app.db.models import EditalRow
    S = make_session(os.environ["MYLIC_DATABASE_URL"])
    with S() as s:
        row = EditalRow(fonte="pncp", chave_natural=chave, hash_conteudo="h", objeto="clipping",
                        orgao_nome="Org", orgao_cnpj="0", uf="AM", modalidade="Pregao",
                        valor_estimado=Decimal("1"), data_publicacao=date(2026, 9, 1),
                        score_relevancia=0.9, status="novo", url_origem="x",
                        capturado_em=datetime.now(timezone.utc))
        s.add(row); s.commit(); return row.id


def test_detalhe_e_patch_status():
    eid = _seed_um()
    from app.api.main import app
    c = TestClient(app)
    assert c.get(f"/editais/{eid}").status_code == 200
    assert c.get("/editais/99999999").status_code == 404
    r = c.patch(f"/editais/{eid}", json={"status": "oportunidade"})
    assert r.status_code == 200 and r.json()["status"] == "oportunidade"
    assert c.patch(f"/editais/{eid}", json={"status": "xpto"}).status_code == 422
```

- [ ] **Step 2: Run to verify it fails** -> FAIL.

- [ ] **Step 3: Implement**

```python
# schemas.py (acrescentar)
from app.domain.edital import StatusCaixa

class ArquivoResumo(BaseModel):
    id: int
    tipo: str
    model_config = {"from_attributes": True}

class EditalDetalhe(EditalResumo):
    orgao_cnpj: str
    municipio: str | None
    motivo_relevancia: str
    url_origem: str
    arquivos: list[ArquivoResumo] = []

class MudarStatus(BaseModel):
    status: StatusCaixa
```

```python
# editais.py (acrescentar)
from fastapi import HTTPException
from app.api.schemas import EditalDetalhe, ArquivoResumo, MudarStatus
from app.db.models import ArquivoEditalRow

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
```

- [ ] **Step 4: Run to verify it passes** -> PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/editais.py app/api/schemas.py tests/api/test_editais_detail.py
git commit -m "feat(api): GET detalhe (com arquivos) + PATCH status do edital"
```

---

### Task 4: `GET /editais/{id}/arquivo/{arquivo_id}` — serve o PDF do disco (contencao de caminho)

**Files:**
- Modify: `app/api/editais.py`
- Test: `tests/api/test_arquivo_serve.py`

**Interfaces:**
- Produces: `GET /editais/{edital_id}/arquivo/{arquivo_id}` -> `FileResponse` do `caminho_local`. So serve se o caminho resolvido estiver DENTRO de `Settings().pdf_dir`; 404 se o arquivo nao e desse edital ou nao existe.

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_arquivo_serve.py
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
```
> Nota: `Settings()` e lido dentro do handler, por isso o `monkeypatch.setenv` do `pdf_dir` tem efeito. Confirma que `deps._sessionmaker` usa a mesma `MYLIC_DATABASE_URL`.

- [ ] **Step 2: Run to verify it fails** -> FAIL.

- [ ] **Step 3: Implement**

```python
# editais.py (acrescentar)
from pathlib import Path
from fastapi.responses import FileResponse
from app.config import Settings

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
```

- [ ] **Step 4: Run to verify it passes** -> PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/editais.py tests/api/test_arquivo_serve.py
git commit -m "feat(api): servir PDF do disco com contencao de caminho (pdf_dir)"
```

---

### Task 5: `GET /digest/hoje`

**Files:**
- Create: `app/api/digest.py`
- Modify: `app/api/main.py`
- Test: `tests/api/test_digest_endpoint.py`

**Interfaces:**
- Produces: `GET /digest/hoje` -> `{data_ref, resumo, destaques}` — `resumo` do ultimo `DigestLogRow` de hoje (ou `{}`), `destaques` = relevantes de hoje (score>=piso, top 20).

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_digest_endpoint.py
import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def test_digest_hoje_devolve_estrutura():
    from app.api.main import app
    c = TestClient(app)
    r = c.get("/digest/hoje")
    assert r.status_code == 200
    body = r.json()
    assert "data_ref" in body and "resumo" in body and "destaques" in body
```

- [ ] **Step 2: Run to verify it fails** -> FAIL.

- [ ] **Step 3: Implement**

```python
# app/api/digest.py
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
```
Registar `from app.api import digest; app.include_router(digest.router)` em `main.py`.

- [ ] **Step 4: Run to verify it passes** -> PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/digest.py app/api/main.py tests/api/test_digest_endpoint.py
git commit -m "feat(api): GET /digest/hoje (resumo do dia + destaques)"
```

---

### Task 6: CRUD `/projetos-interesse` + filtro `projeto_id` na lista

**Files:**
- Create: `app/api/projetos.py`
- Modify: `app/api/main.py`, `app/api/editais.py`, `app/api/schemas.py`
- Test: `tests/api/test_projetos.py`

**Interfaces:**
- Produces: `ProjetoIn` (nome, palavras_chave, filtros, ativo=True), `ProjetoOut` (+id, criado_em). `GET/POST(201)/PUT/DELETE(204) /projetos-interesse`. `GET /editais?projeto_id=N` aplica OR de `ilike` das palavras + filtros uf/modalidade do projeto.

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_projetos.py
import os, pytest
pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")
from fastapi.testclient import TestClient


def test_crud_projeto_e_filtro():
    from app.api.main import app
    c = TestClient(app)
    r = c.post("/projetos-interesse", json={"nome": "DJE Nordeste",
              "palavras_chave": ["dje", "clipping"], "filtros": {"uf": "AM"}})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert any(p["id"] == pid for p in c.get("/projetos-interesse").json())
    assert c.put(f"/projetos-interesse/{pid}", json={"nome": "DJE NE", "palavras_chave": ["dje"],
                 "filtros": {}, "ativo": False}).status_code == 200
    assert c.get("/editais", params={"projeto_id": pid}).status_code == 200
    assert c.delete(f"/projetos-interesse/{pid}").status_code == 204
```

- [ ] **Step 2: Run to verify it fails** -> FAIL.

- [ ] **Step 3: Implement**

```python
# schemas.py (acrescentar)
from datetime import datetime

class ProjetoIn(BaseModel):
    nome: str
    palavras_chave: list[str] = []
    filtros: dict = {}
    ativo: bool = True

class ProjetoOut(ProjetoIn):
    id: int
    criado_em: datetime
    model_config = {"from_attributes": True}
```

```python
# app/api/projetos.py
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
```

Em `editais.py`, `listar` aceita `projeto_id: int | None = None`; se dado, carrega o projeto e aplica:
```python
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
```
Regista `from app.api import projetos; app.include_router(projetos.router)` no `main.py`.

- [ ] **Step 4: Run to verify it passes** -> PASS; `lint-imports` KEPT.

- [ ] **Step 5: Commit**

```bash
git add app/api/projetos.py app/api/main.py app/api/editais.py app/api/schemas.py tests/api/test_projetos.py
git commit -m "feat(api): CRUD projetos-interesse + filtro projeto_id na lista"
```

---

## Self-Review

**Spec coverage (design §8, PRD 1.8):** listar+filtros+busca (T2), detalhe+arquivos (T3), PATCH status (T3), servir PDF (T4), digest do dia (T5), projetos CRUD (T6); gap do 1A (arquivo_edital) fechado (T1). Auth ausente por decisao (localhost). `projeto_id` adiado de T2 -> T6 (Ruling explicito).

**Placeholder scan:** sem TBD; unico adiamento (`projeto_id`) e explicito e implementado em T6.

**Type consistency:** `upsert_editais` muda para `(ids, novos)` em T1 e o orquestrador + teste sao atualizados no mesmo passo; `EditalResumo`/`EditalDetalhe`/`Pagina`/`ArquivoResumo`/`ProjetoIn/Out`/`MudarStatus` coerentes; `MudarStatus.status: StatusCaixa` reusa o enum do dominio (422 automatico).

## Nota de execucao
Todas as tasks exigem **Postgres** (Docker up, porta 5433); testes `skipif` sem `MYLIC_DATABASE_URL`. O plano do **frontend Next.js** (caixa, digest, projetos, tokens do LexFlow copiados, Playwright E2E) escreve-se a seguir a este, quando a API estiver verde.
