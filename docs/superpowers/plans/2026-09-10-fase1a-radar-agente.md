# Fase 1A — Agente Radar de Editais (backend) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um agente autónomo que, num comando diário, captura editais do PNCP e do Compras.gov.br, classifica relevância tipo-LexFlow por léxico, baixa os PDFs dos relevantes, persiste em Postgres e envia um digest por e-mail + Telegram + registo de página.

**Architecture:** Hexagonal. Domínio puro (relevância, dedup, digest) sem I/O; portas `FonteEditais`/`ArmazenamentoEditalPdf`/`CanalDigest`/`ClassificadorRelevancia`; adaptadores para PNCP, Compras.gov, disco, e-mail, Telegram. Um orquestrador `run_daily()` corre por fonte com isolamento de falhas e janela incremental; disparado por agendador do SO (Task Scheduler/cron), não por processo residente.

**Tech Stack:** Python 3.12, uv, SQLAlchemy 2.0 (sync), Alembic, httpx, pydantic, PostgreSQL (docker), stdlib (smtplib, hashlib, unicodedata). Dev: pytest, import-linter.

**Spec:** [`docs/superpowers/specs/2026-09-10-radar-editais-lexflow-design.md`](../specs/2026-09-10-radar-editais-lexflow-design.md) e [`docs/prd/radar-editais-lexflow/requirements.md`](../../prd/radar-editais-lexflow/requirements.md)

## Global Constraints

- Python **3.12**; dependências no `pyproject.toml`, fixadas no `uv.lock`; instalar com `uv sync --frozen`. **Sem `requirements.txt`.**
- `app/domain/` **não importa** SQLAlchemy, FastAPI, httpx, pydantic nem `app.adapters`/`app.db` (contrato import-linter `forbidden-domain`).
- Portas **devolvem tipos de domínio**, nunca `dict`/JSON cru.
- Escolha de fonte/armazenamento/classificador **por configuração na construção**, nunca por `if` dentro do orquestrador.
- Segredos só em `.env` (SMTP, Telegram). `.env` e a pasta de PDFs **nunca** versionados.
- TDD estrito: teste vermelho pela razão certa antes do código. Commits frequentes.
- Datas das APIs em `AAAAMMDD`; no domínio/BD usar `date`/`datetime` timezone-aware (UTC).

---

### Task 1: Fundações do projeto

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `.env.example`, `.importlinter`, `docker-compose.yml`
- Create: `app/__init__.py`, `app/domain/__init__.py`, `app/ports/__init__.py`, `app/adapters/__init__.py`, `app/db/__init__.py`, `app/config.py`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Consumes: nada.
- Produces: pacote `app` importável; `app.config.Settings` (pydantic-settings) com `database_url: str`, `pncp_base_url: str = "https://pncp.gov.br/api/consulta"`, `compras_base_url: str = "https://dadosabertos.compras.gov.br"`, `pdf_dir: str`, `smtp_*`, `telegram_bot_token: str | None`, `telegram_chat_id: str | None`, `janela_inicial_dias: int = 7`, `score_piso: float = 0.34`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
def test_importa_app_e_config():
    from app.config import Settings
    s = Settings(database_url="postgresql+psycopg://u:p@localhost/db", pdf_dir="/tmp/pdfs")
    assert s.pncp_base_url.endswith("/api/consulta")
    assert s.score_piso == 0.34
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: FAIL (`ModuleNotFoundError: app.config`).

- [ ] **Step 3: Create project scaffolding**

`pyproject.toml`:
```toml
[project]
name = "mylicitacoes"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "sqlalchemy>=2.0",
  "alembic>=1.13",
  "psycopg[binary]>=3.2",
  "httpx>=0.27",
  "certifi>=2024.0",
  "pydantic>=2.7",
  "pydantic-settings>=2.3",
]

[dependency-groups]
dev = ["pytest>=8", "import-linter>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

`app/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MYLIC_", env_file=".env", extra="ignore")

    database_url: str
    pdf_dir: str
    pncp_base_url: str = "https://pncp.gov.br/api/consulta"
    compras_base_url: str = "https://dadosabertos.compras.gov.br"
    janela_inicial_dias: int = 7
    score_piso: float = 0.34
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_to: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
```

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
/pdfs/
.pytest_cache/
```

`.env.example`:
```
MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5432/mylic
MYLIC_PDF_DIR=./pdfs
MYLIC_SMTP_HOST=
MYLIC_SMTP_USER=
MYLIC_SMTP_PASSWORD=
MYLIC_SMTP_FROM=
MYLIC_SMTP_TO=
MYLIC_TELEGRAM_BOT_TOKEN=
MYLIC_TELEGRAM_CHAT_ID=
```

`.importlinter`:
```ini
[importlinter]
root_package = app

[importlinter:contract:forbidden-domain]
name = Dominio nao depende de framework nem adapters
type = forbidden
source_modules = app.domain
forbidden_modules =
    sqlalchemy
    httpx
    fastapi
    pydantic
    app.adapters
    app.db
```

`docker-compose.yml`:
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: mylic
      POSTGRES_PASSWORD: mylic
      POSTGRES_DB: mylic
    ports: ["5432:5432"]
```

Create the empty `__init__.py` files listed under **Files**.

- [ ] **Step 4: Run test + import-linter**

Run: `uv sync && uv run pytest tests/test_smoke.py -v && uv run lint-imports`
Expected: test PASS; import-linter `forbidden-domain` KEPT.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock .gitignore .env.example .importlinter docker-compose.yml app tests/test_smoke.py
git commit -m "chore: fundacoes do projeto MyLicitacoes (hexagonal + config + import-linter)"
```

---

### Task 2: Domínio — Edital e enums

**Files:**
- Create: `app/domain/edital.py`
- Test: `tests/domain/test_edital.py`

**Interfaces:**
- Produces:
  - `class Fonte(StrEnum): PNCP="pncp"; COMPRAS_GOV="compras_gov"`
  - `class StatusCaixa(StrEnum): NOVO="novo"; LIDO="lido"; ARQUIVADO="arquivado"; OPORTUNIDADE="oportunidade"`
  - `class TipoArquivo(StrEnum): EDITAL="edital"; TR="tr"; ETP="etp"; PB="pb"`
  - `@dataclass(frozen=True) class Edital` com: `fonte: Fonte`, `chave_natural: str`, `objeto: str`, `orgao_nome: str`, `orgao_cnpj: str`, `uf: str | None`, `municipio: str | None`, `modalidade: str | None`, `valor_estimado: Decimal | None`, `data_publicacao: date | None`, `data_abertura: date | None`, `data_fim_propostas: date | None`, `url_origem: str`, `texto_extra: str = ""` (texto adicional p/ matching, ex. itens).
  - `@dataclass(frozen=True) class ArquivoRef` com `tipo: TipoArquivo`, `url: str`, `nome: str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/domain/test_edital.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte, StatusCaixa


def test_edital_e_imutavel_e_tem_chave():
    e = Edital(
        fonte=Fonte.PNCP, chave_natural="00000000000191-2026-42",
        objeto="Contratacao de servico de clipping", orgao_nome="TJ",
        orgao_cnpj="00000000000191", uf="AM", municipio="Manaus",
        modalidade="Pregao", valor_estimado=Decimal("1000"),
        data_publicacao=date(2026, 9, 1), data_abertura=None,
        data_fim_propostas=None, url_origem="https://pncp.gov.br/x",
    )
    assert e.fonte == Fonte.PNCP
    assert StatusCaixa.NOVO == "novo"
    import dataclasses
    try:
        e.objeto = "x"  # frozen
        assert False
    except dataclasses.FrozenInstanceError:
        pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/domain/test_edital.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

```python
# app/domain/edital.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum


class Fonte(StrEnum):
    PNCP = "pncp"
    COMPRAS_GOV = "compras_gov"


class StatusCaixa(StrEnum):
    NOVO = "novo"
    LIDO = "lido"
    ARQUIVADO = "arquivado"
    OPORTUNIDADE = "oportunidade"


class TipoArquivo(StrEnum):
    EDITAL = "edital"
    TR = "tr"
    ETP = "etp"
    PB = "pb"


@dataclass(frozen=True)
class Edital:
    fonte: Fonte
    chave_natural: str
    objeto: str
    orgao_nome: str
    orgao_cnpj: str
    uf: str | None
    municipio: str | None
    modalidade: str | None
    valor_estimado: Decimal | None
    data_publicacao: date | None
    data_abertura: date | None
    data_fim_propostas: date | None
    url_origem: str
    texto_extra: str = ""


@dataclass(frozen=True)
class ArquivoRef:
    tipo: TipoArquivo
    url: str
    nome: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/domain/test_edital.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/domain/edital.py tests/domain/test_edital.py
git commit -m "feat(domain): entidade Edital e enums"
```

---

### Task 3: Domínio — classificador de relevância por léxico

**Files:**
- Create: `app/domain/relevancia.py`, `app/domain/lexico.py`
- Test: `tests/domain/test_relevancia.py`

**Interfaces:**
- Consumes: `Edital` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class Lexico: positivos: frozenset[str]; negativos: frozenset[str]`
  - `@dataclass(frozen=True) class ScoreRelevancia: valor: float; termos: tuple[str, ...]`
  - `LEXICO_TIPO_LEXFLOW: Lexico` em `lexico.py`.
  - `def classificar_relevancia(objeto: str, texto: str, lexico: Lexico) -> ScoreRelevancia` — normaliza (minúsculas, sem acentos), conta positivos distintos presentes, subtrai negativos; `valor = max(0, positivos_encontrados - negativos_encontrados) / total_positivos_do_lexico`; `termos` = positivos encontrados.

- [ ] **Step 1: Write the failing test**

```python
# tests/domain/test_relevancia.py
from app.domain.relevancia import classificar_relevancia, Lexico, ScoreRelevancia

LX = Lexico(
    positivos=frozenset({"clipping", "monitoramento de publicacoes", "diario de justica", "dje"}),
    negativos=frozenset({"merenda escolar"}),
)


def test_objeto_tipo_lexflow_pontua_alto():
    s = classificar_relevancia("Contratação de CLIPPING e monitoramento de publicações", "", LX)
    assert isinstance(s, ScoreRelevancia)
    assert s.valor >= 0.5
    assert "clipping" in s.termos


def test_objeto_irrelevante_pontua_zero():
    s = classificar_relevancia("Aquisição de merenda escolar", "para as escolas", LX)
    assert s.valor == 0.0


def test_acentos_e_caixa_nao_importam():
    s = classificar_relevancia("DIÁRIO DE JUSTIÇA eletrônico", "", LX)
    assert "diario de justica" in s.termos
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/domain/test_relevancia.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

```python
# app/domain/relevancia.py
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Lexico:
    positivos: frozenset[str]
    negativos: frozenset[str]


@dataclass(frozen=True)
class ScoreRelevancia:
    valor: float
    termos: tuple[str, ...]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def classificar_relevancia(objeto: str, texto: str, lexico: Lexico) -> ScoreRelevancia:
    alvo = _norm(f"{objeto} {texto}")
    achados = tuple(t for t in sorted(lexico.positivos) if _norm(t) in alvo)
    neg = sum(1 for t in lexico.negativos if _norm(t) in alvo)
    total = len(lexico.positivos) or 1
    valor = max(0, len(achados) - neg) / total
    return ScoreRelevancia(valor=valor, termos=achados)
```

```python
# app/domain/lexico.py
from app.domain.relevancia import Lexico

LEXICO_TIPO_LEXFLOW = Lexico(
    positivos=frozenset({
        "clipping",
        "monitoramento de publicacoes",
        "monitoramento de publicacoes oficiais",
        "recorte de publicacoes",
        "recorte de materias",
        "diario de justica",
        "diario oficial",
        "dje",
        "acompanhamento processual",
        "captura de publicacoes",
        "software juridico",
        "sistema juridico",
        "gestao de publicacoes",
        "publicacoes oficiais",
    }),
    negativos=frozenset({
        "merenda escolar",
        "material de construcao",
        "combustivel",
    }),
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/domain/test_relevancia.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/domain/relevancia.py app/domain/lexico.py tests/domain/test_relevancia.py
git commit -m "feat(domain): classificador de relevancia por lexico (accent-fold, score por cobertura)"
```

---

### Task 4: Domínio — dedup

**Files:**
- Create: `app/domain/dedup.py`
- Test: `tests/domain/test_dedup.py`

**Interfaces:**
- Consumes: `Edital` (Task 2).
- Produces:
  - `def hash_conteudo(e: Edital) -> str` — sha256 hex de objeto+orgao+datas.
  - `def deduplicar(editais: Iterable[Edital]) -> list[Edital]` — colapsa por `(fonte, chave_natural)`, mantendo o último; e entre fontes por `(orgao_cnpj, objeto normalizado, data_publicacao)` mantendo preferencialmente PNCP.

- [ ] **Step 1: Write the failing test**

```python
# tests/domain/test_dedup.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte
from app.domain.dedup import deduplicar, hash_conteudo


def _ed(fonte, chave, objeto="Servico de clipping", cnpj="00000000000191", pub=date(2026, 9, 1)):
    return Edital(fonte, chave, objeto, "Org", cnpj, "AM", "Manaus", "Pregao",
                  Decimal("1"), pub, None, None, "http://x")


def test_dedup_por_chave_natural():
    a = _ed(Fonte.PNCP, "k1")
    b = _ed(Fonte.PNCP, "k1")
    assert len(deduplicar([a, b])) == 1


def test_dedup_entre_fontes_prefere_pncp():
    p = _ed(Fonte.PNCP, "kp")
    c = _ed(Fonte.COMPRAS_GOV, "kc")
    out = deduplicar([c, p])
    assert len(out) == 1
    assert out[0].fonte == Fonte.PNCP


def test_hash_muda_com_conteudo():
    assert hash_conteudo(_ed(Fonte.PNCP, "k", objeto="A")) != hash_conteudo(_ed(Fonte.PNCP, "k", objeto="B"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/domain/test_dedup.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/domain/dedup.py
import hashlib
import unicodedata
from collections.abc import Iterable
from app.domain.edital import Edital, Fonte


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c)).strip()


def hash_conteudo(e: Edital) -> str:
    base = f"{e.objeto}|{e.orgao_cnpj}|{e.data_publicacao}|{e.data_abertura}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def deduplicar(editais: Iterable[Edital]) -> list[Edital]:
    por_chave: dict[tuple[Fonte, str], Edital] = {}
    for e in editais:
        por_chave[(e.fonte, e.chave_natural)] = e
    entre_fontes: dict[tuple[str, str, object], Edital] = {}
    for e in por_chave.values():
        k = (e.orgao_cnpj, _norm(e.objeto), e.data_publicacao)
        atual = entre_fontes.get(k)
        if atual is None or (e.fonte == Fonte.PNCP and atual.fonte != Fonte.PNCP):
            entre_fontes[k] = e
    return list(entre_fontes.values())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/domain/test_dedup.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/domain/dedup.py tests/domain/test_dedup.py
git commit -m "feat(domain): dedup por chave natural e entre fontes (prefere PNCP)"
```

---

### Task 5: Domínio — modelo e montagem do digest

**Files:**
- Create: `app/domain/digest.py`
- Test: `tests/domain/test_digest.py`

**Interfaces:**
- Consumes: `Edital` (Task 2).
- Produces:
  - `@dataclass(frozen=True) class LinhaProjeto: nome: str; novos: int; prazo_a_fechar: int`
  - `@dataclass(frozen=True) class Digest: data_ref: date; total_novos: int; total_relevantes: int; total_downloads: int; fontes_com_falha: tuple[str, ...]; destaques: tuple[Edital, ...]; projetos: tuple[LinhaProjeto, ...]`
  - `def montar_digest(data_ref, relevantes, novos_total, downloads, fontes_falha, projetos_linhas, max_destaques=10) -> Digest`

- [ ] **Step 1: Write the failing test**

```python
# tests/domain/test_digest.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte
from app.domain.digest import montar_digest, LinhaProjeto


def _ed(o):
    return Edital(Fonte.PNCP, o, o, "Org", "00000000000191", "AM", "Manaus",
                  "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")


def test_digest_conta_e_limita_destaques():
    rel = [_ed(f"clipping {i}") for i in range(15)]
    d = montar_digest(date(2026, 9, 1), rel, novos_total=40, downloads=15,
                      fontes_falha=("compras_gov",),
                      projetos_linhas=[LinhaProjeto("DJE Nordeste", 3, 1)])
    assert d.total_relevantes == 15
    assert d.total_novos == 40
    assert len(d.destaques) == 10
    assert d.fontes_com_falha == ("compras_gov",)
    assert d.projetos[0].nome == "DJE Nordeste"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/domain/test_digest.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/domain/digest.py
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from app.domain.edital import Edital


@dataclass(frozen=True)
class LinhaProjeto:
    nome: str
    novos: int
    prazo_a_fechar: int


@dataclass(frozen=True)
class Digest:
    data_ref: date
    total_novos: int
    total_relevantes: int
    total_downloads: int
    fontes_com_falha: tuple[str, ...]
    destaques: tuple[Edital, ...]
    projetos: tuple[LinhaProjeto, ...]


def montar_digest(data_ref: date, relevantes: Sequence[Edital], novos_total: int,
                  downloads: int, fontes_falha: Sequence[str],
                  projetos_linhas: Sequence[LinhaProjeto], max_destaques: int = 10) -> Digest:
    return Digest(
        data_ref=data_ref,
        total_novos=novos_total,
        total_relevantes=len(relevantes),
        total_downloads=downloads,
        fontes_com_falha=tuple(fontes_falha),
        destaques=tuple(relevantes[:max_destaques]),
        projetos=tuple(projetos_linhas),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/domain/test_digest.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/domain/digest.py tests/domain/test_digest.py
git commit -m "feat(domain): modelo e montagem do digest diario"
```

---

### Task 6: Portas + adaptador classificador keyword

**Files:**
- Create: `app/ports/portas.py`, `app/adapters/classificador/keyword.py`, `app/adapters/classificador/__init__.py`
- Test: `tests/adapters/test_classificador_keyword.py`

**Interfaces:**
- Consumes: `Edital`, `ArquivoRef`, `ScoreRelevancia`, `Lexico`, `Digest`.
- Produces (Protocols em `app/ports/portas.py`):
  - `class FonteEditais(Protocol): nome: str; def buscar(self, inicio: date, fim: date) -> list[Edital]: ...; def listar_arquivos(self, e: Edital) -> list[ArquivoRef]: ...`
  - `class ClassificadorRelevancia(Protocol): def classificar(self, e: Edital) -> ScoreRelevancia: ...`
  - `class ArmazenamentoEditalPdf(Protocol): def guardar(self, e: Edital, arq: ArquivoRef, conteudo: bytes) -> str: ...` (devolve caminho)
  - `class CanalDigest(Protocol): def enviar(self, d: Digest) -> None: ...`
  - Adaptador `KeywordClassificador(lexico: Lexico)` implementando `ClassificadorRelevancia` via `classificar_relevancia(e.objeto, e.texto_extra, lexico)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_classificador_keyword.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte
from app.domain.lexico import LEXICO_TIPO_LEXFLOW
from app.adapters.classificador.keyword import KeywordClassificador


def test_keyword_classificador_usa_lexico():
    c = KeywordClassificador(LEXICO_TIPO_LEXFLOW)
    e = Edital(Fonte.PNCP, "k", "Servico de clipping e DJE", "Org", "00000000000191",
               "AM", "Manaus", "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")
    s = c.classificar(e)
    assert s.valor > 0
    assert "clipping" in s.termos
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_classificador_keyword.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/ports/portas.py
from datetime import date
from typing import Protocol
from app.domain.edital import Edital, ArquivoRef
from app.domain.relevancia import ScoreRelevancia
from app.domain.digest import Digest


class FonteEditais(Protocol):
    nome: str
    def buscar(self, inicio: date, fim: date) -> list[Edital]: ...
    def listar_arquivos(self, e: Edital) -> list[ArquivoRef]: ...


class ClassificadorRelevancia(Protocol):
    def classificar(self, e: Edital) -> ScoreRelevancia: ...


class ArmazenamentoEditalPdf(Protocol):
    def guardar(self, e: Edital, arq: ArquivoRef, conteudo: bytes) -> str: ...


class CanalDigest(Protocol):
    def enviar(self, d: Digest) -> None: ...
```

```python
# app/adapters/classificador/keyword.py
from app.domain.edital import Edital
from app.domain.relevancia import Lexico, ScoreRelevancia, classificar_relevancia


class KeywordClassificador:
    def __init__(self, lexico: Lexico) -> None:
        self._lexico = lexico

    def classificar(self, e: Edital) -> ScoreRelevancia:
        return classificar_relevancia(e.objeto, e.texto_extra, self._lexico)
```

- [ ] **Step 4: Run test + import-linter**

Run: `uv run pytest tests/adapters/test_classificador_keyword.py -v && uv run lint-imports`
Expected: PASS; contrato KEPT.

- [ ] **Step 5: Commit**

```bash
git add app/ports/portas.py app/adapters/classificador tests/adapters/test_classificador_keyword.py
git commit -m "feat(ports): protocolos das portas + adaptador classificador keyword"
```

---

### Task 7: Cliente HTTP com TLS robusto e retry

**Files:**
- Create: `app/adapters/http_client.py`
- Test: `tests/adapters/test_http_client.py`

**Interfaces:**
- Produces: `def make_client(base_url: str, timeout: float = 30.0) -> httpx.Client` — cria `httpx.Client` com `ssl.create_default_context(cafile=certifi.where())`, `follow_redirects=True`, e `transport=httpx.HTTPTransport(retries=3, verify=ctx)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_http_client.py
import httpx
from app.adapters.http_client import make_client


def test_make_client_config():
    c = make_client("https://example.test")
    assert isinstance(c, httpx.Client)
    assert str(c.base_url).startswith("https://example.test")
    c.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_http_client.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/adapters/http_client.py
import ssl
import certifi
import httpx


def make_client(base_url: str, timeout: float = 30.0) -> httpx.Client:
    ctx = ssl.create_default_context(cafile=certifi.where())
    transport = httpx.HTTPTransport(retries=3, verify=ctx)
    return httpx.Client(base_url=base_url, timeout=timeout,
                        follow_redirects=True, transport=transport,
                        headers={"User-Agent": "MyLicitacoes/0.1 (radar de editais)"})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_http_client.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/adapters/http_client.py tests/adapters/test_http_client.py
git commit -m "feat(adapters): cliente HTTP com TLS via certifi e retry"
```

---

### Task 8: Adaptador PNCP — capturar fixture real e escrever o parser

> ⚠️ Este é o único ponto onde os nomes de campos do JSON precisam de ser
> confirmados contra a API real. NÃO inventar chaves: capturar o fixture primeiro.

**Files:**
- Create: `app/adapters/fontes/pncp.py`, `app/adapters/fontes/__init__.py`
- Create: `tests/fixtures/pncp_publicacao.json` (capturado da API real)
- Test: `tests/adapters/test_pncp.py`

**Interfaces:**
- Consumes: `Edital`, `Fonte`, `ArquivoRef`, `TipoArquivo`, `make_client` (Task 7).
- Produces: `class FontePncp` implementando `FonteEditais` (`nome="pncp"`), com `buscar`, `listar_arquivos` e `_parse_item(item: dict) -> Edital` (função de módulo, testável isoladamente).

- [ ] **Step 1: Capturar o fixture real (uma vez)**

Run (PowerShell), guardando a resposta:
```bash
uv run python -c "import httpx,ssl,certifi,json; ctx=ssl.create_default_context(cafile=certifi.where()); r=httpx.get('https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao', params={'dataInicial':'20260901','dataFinal':'20260902','codigoModalidadeContratacao':8,'pagina':1,'tamanhoPagina':10}, verify=ctx, timeout=60); open('tests/fixtures/pncp_publicacao.json','w',encoding='utf-8').write(json.dumps(r.json(), ensure_ascii=False, indent=2)); print(r.status_code, len(r.json().get('data',[])))"
```
Expected: `200` e alguns itens. **Abrir o ficheiro e ler os nomes reais dos campos** (`data[].objetoCompra`? `orgaoEntidade.cnpj`? `anoCompra`? `sequencialCompra`? `unidadeOrgao.ufSigla`? `dataAberturaProposta`?). Ajustar o mapeamento no Step 3 aos nomes observados.

- [ ] **Step 2: Write the failing test (contra o fixture)**

```python
# tests/adapters/test_pncp.py
import json
from pathlib import Path
from app.adapters.fontes.pncp import _parse_item
from app.domain.edital import Edital, Fonte

FIX = json.loads(Path("tests/fixtures/pncp_publicacao.json").read_text(encoding="utf-8"))


def test_parse_item_primeiro_registo():
    item = FIX["data"][0]
    e = _parse_item(item)
    assert isinstance(e, Edital)
    assert e.fonte == Fonte.PNCP
    assert e.orgao_cnpj and e.chave_natural.count("-") == 2
    assert e.objeto  # objeto não vazio
```

- [ ] **Step 3: Write minimal implementation (mapeando aos campos observados)**

```python
# app/adapters/fontes/pncp.py
from datetime import date, datetime
from decimal import Decimal
from app.adapters.http_client import make_client
from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo

MODALIDADES = (6, 7, 8, 9, 12)  # confirmar codigos observados no fixture/manual


def _d(s: str | None) -> date | None:
    if not s:
        return None
    return datetime.fromisoformat(str(s).replace("Z", "+00:00")).date()


def _parse_item(item: dict) -> Edital:
    orgao = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    cnpj = str(orgao.get("cnpj") or "")
    ano = item.get("anoCompra")
    seq = item.get("sequencialCompra")
    valor = item.get("valorTotalEstimado")
    return Edital(
        fonte=Fonte.PNCP,
        chave_natural=f"{cnpj}-{ano}-{seq}",
        objeto=str(item.get("objetoCompra") or ""),
        orgao_nome=str(orgao.get("razaoSocial") or ""),
        orgao_cnpj=cnpj,
        uf=unidade.get("ufSigla"),
        municipio=unidade.get("municipioNome"),
        modalidade=item.get("modalidadeNome"),
        valor_estimado=Decimal(str(valor)) if valor is not None else None,
        data_publicacao=_d(item.get("dataPublicacaoPncp")),
        data_abertura=_d(item.get("dataAberturaProposta")),
        data_fim_propostas=_d(item.get("dataEncerramentoProposta")),
        url_origem=f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}",
    )


class FontePncp:
    nome = "pncp"

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def buscar(self, inicio: date, fim: date) -> list[Edital]:
        out: list[Edital] = []
        di, df = inicio.strftime("%Y%m%d"), fim.strftime("%Y%m%d")
        with make_client(self._base_url) as c:
            for mod in MODALIDADES:
                pagina = 1
                while True:
                    r = c.get("/v1/contratacoes/publicacao", params={
                        "dataInicial": di, "dataFinal": df,
                        "codigoModalidadeContratacao": mod,
                        "pagina": pagina, "tamanhoPagina": 500,
                    })
                    if r.status_code == 204:
                        break
                    r.raise_for_status()
                    body = r.json()
                    itens = body.get("data") or []
                    out.extend(_parse_item(i) for i in itens)
                    if pagina >= int(body.get("totalPaginas") or 1):
                        break
                    pagina += 1
        return out

    def listar_arquivos(self, e: Edital) -> list[ArquivoRef]:
        cnpj, ano, seq = e.chave_natural.split("-")
        with make_client(self._base_url) as c:
            r = c.get(f"/v1/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos")
            if r.status_code == 204:
                return []
            r.raise_for_status()
            refs = []
            for a in r.json():
                refs.append(ArquivoRef(tipo=TipoArquivo.EDITAL,
                                       url=a.get("url") or a.get("uri") or "",
                                       nome=a.get("titulo") or a.get("nomeArquivo") or "arquivo"))
            return refs
```

> Se um nome de campo do fixture diferir (ex.: `objetoCompra`), corrigir aqui para
> o nome real observado e re-correr o teste.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_pncp.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/adapters/fontes/pncp.py tests/adapters/test_pncp.py tests/fixtures/pncp_publicacao.json
git commit -m "feat(adapters): fonte PNCP (busca por publicacao + parser contra fixture real + arquivos)"
```

---

### Task 9: Adaptador Compras.gov.br — fixture real + parser

**Files:**
- Create: `app/adapters/fontes/compras_gov.py`
- Create: `tests/fixtures/compras_gov.json`
- Test: `tests/adapters/test_compras_gov.py`

**Interfaces:**
- Consumes: `Edital`, `Fonte`, `ArquivoRef`, `make_client`.
- Produces: `class FonteComprasGov` implementando `FonteEditais` (`nome="compras_gov"`), com `_parse_item(item: dict) -> Edital` e `buscar(inicio, fim)`. `listar_arquivos` devolve `[]` no MVP (os PDFs só do PNCP baixam na Fase 1).

- [ ] **Step 1: Capturar o fixture real**

Consultar o Swagger em `https://dadosabertos.compras.gov.br/swagger-ui/index.html`, escolher o endpoint de **licitações/contratações por data**, e capturar um exemplo (ajustar caminho/params ao endpoint real):
```bash
uv run python -c "import httpx,ssl,certifi,json; ctx=ssl.create_default_context(cafile=certifi.where()); r=httpx.get('https://dadosabertos.compras.gov.br/modulo-legado/1_consultarLicitacao', params={'pagina':1,'tamanhoPagina':10,'data_publicacao_inicial':'2026-09-01','data_publicacao_final':'2026-09-02'}, verify=ctx, timeout=60); print(r.status_code); open('tests/fixtures/compras_gov.json','w',encoding='utf-8').write(json.dumps(r.json(), ensure_ascii=False, indent=2))"
```

- [ ] **Step 2: Write the failing test**

```python
# tests/adapters/test_compras_gov.py
import json
from pathlib import Path
from app.adapters.fontes.compras_gov import _parse_item
from app.domain.edital import Edital, Fonte

FIX = json.loads(Path("tests/fixtures/compras_gov.json").read_text(encoding="utf-8"))


def test_parse_item():
    itens = FIX.get("resultado") or FIX.get("data") or FIX.get("_embedded", {}).get("licitacoes") or []
    e = _parse_item(itens[0])
    assert isinstance(e, Edital)
    assert e.fonte == Fonte.COMPRAS_GOV
    assert e.objeto
```

- [ ] **Step 3: Write minimal implementation (mapeando aos campos observados)**

```python
# app/adapters/fontes/compras_gov.py
# Endpoint usado: <colar o caminho real observado no Swagger>
from datetime import date, datetime
from decimal import Decimal
from app.adapters.http_client import make_client
from app.domain.edital import Edital, Fonte, ArquivoRef


def _d(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s)[:19]).date()
    except ValueError:
        return None


def _parse_item(item: dict) -> Edital:
    cnpj = str(item.get("cnpj_orgao") or item.get("cnpjOrgao") or "")
    ident = str(item.get("identificador") or item.get("numero") or item.get("id") or "")
    valor = item.get("valor_estimado") or item.get("valorEstimado")
    return Edital(
        fonte=Fonte.COMPRAS_GOV,
        chave_natural=ident or f"{cnpj}-{item.get('numero','')}",
        objeto=str(item.get("objeto") or item.get("descricao") or ""),
        orgao_nome=str(item.get("nome_orgao") or item.get("orgao") or ""),
        orgao_cnpj=cnpj,
        uf=item.get("uf"),
        municipio=item.get("municipio"),
        modalidade=item.get("modalidade"),
        valor_estimado=Decimal(str(valor)) if valor is not None else None,
        data_publicacao=_d(item.get("data_publicacao") or item.get("dataPublicacao")),
        data_abertura=_d(item.get("data_abertura") or item.get("dataAbertura")),
        data_fim_propostas=None,
        url_origem=str(item.get("_links", {}).get("self", {}).get("href") or "https://compras.gov.br"),
    )


class FonteComprasGov:
    nome = "compras_gov"

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def buscar(self, inicio: date, fim: date) -> list[Edital]:
        out: list[Edital] = []
        with make_client(self._base_url) as c:
            pagina = 1
            while True:
                r = c.get("/modulo-legado/1_consultarLicitacao", params={
                    "pagina": pagina, "tamanhoPagina": 500,
                    "data_publicacao_inicial": inicio.isoformat(),
                    "data_publicacao_final": fim.isoformat(),
                })
                if r.status_code in (204, 404):
                    break
                r.raise_for_status()
                body = r.json()
                itens = body.get("resultado") or body.get("data") or []
                out.extend(_parse_item(i) for i in itens)
                total_pag = int(body.get("totalPaginas") or 1)
                if not itens or pagina >= total_pag:
                    break
                pagina += 1
        return out

    def listar_arquivos(self, e: Edital) -> list[ArquivoRef]:
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_compras_gov.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/adapters/fontes/compras_gov.py tests/adapters/test_compras_gov.py tests/fixtures/compras_gov.json
git commit -m "feat(adapters): fonte Compras.gov.br (parser contra fixture real)"
```

---

### Task 10: Armazenamento de PDF em disco

**Files:**
- Create: `app/adapters/armazenamento/disco.py`, `app/adapters/armazenamento/__init__.py`
- Test: `tests/adapters/test_armazenamento_disco.py`

**Interfaces:**
- Consumes: `Edital`, `ArquivoRef`.
- Produces: `class ArmazenamentoDisco(base_dir: str)` implementando `ArmazenamentoEditalPdf`; `guardar(e, arq, conteudo) -> str` grava em `base_dir/<fonte>/<chave_natural>/<nome>` e devolve o caminho absoluto; cria dirs; nome saneado.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_armazenamento_disco.py
from datetime import date
from decimal import Decimal
from pathlib import Path
from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo
from app.adapters.armazenamento.disco import ArmazenamentoDisco


def test_guarda_pdf(tmp_path):
    e = Edital(Fonte.PNCP, "00000000000191-2026-42", "clipping", "Org", "00000000000191",
               "AM", "Manaus", "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")
    arq = ArquivoRef(TipoArquivo.EDITAL, "http://x/edital.pdf", "edital.pdf")
    store = ArmazenamentoDisco(str(tmp_path))
    caminho = store.guardar(e, arq, b"%PDF-1.4 conteudo")
    p = Path(caminho)
    assert p.exists()
    assert p.read_bytes().startswith(b"%PDF")
    assert "00000000000191-2026-42" in caminho
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_armazenamento_disco.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/adapters/armazenamento/disco.py
import re
from pathlib import Path
from app.domain.edital import Edital, ArquivoRef


def _sane(nome: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", nome) or "arquivo"


class ArmazenamentoDisco:
    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir)

    def guardar(self, e: Edital, arq: ArquivoRef, conteudo: bytes) -> str:
        destino = self._base / e.fonte.value / _sane(e.chave_natural) / _sane(arq.nome)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return str(destino.resolve())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_armazenamento_disco.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/adapters/armazenamento tests/adapters/test_armazenamento_disco.py
git commit -m "feat(adapters): armazenamento de PDF em disco"
```

---

### Task 11: Persistência — modelos, engine, repositório e Alembic

**Files:**
- Create: `app/db/base.py`, `app/db/models.py`, `app/db/repo.py`, `app/db/engine.py`
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/inicial_edital_20260910.py`
- Test: `tests/db/test_repo.py` (integração, Postgres real)

**Interfaces:**
- Consumes: `Edital`, `Fonte`, `ScoreRelevancia`, `hash_conteudo`.
- Produces:
  - Modelos: `EditalRow`, `ArquivoEditalRow`, `ProjetoInteresseRow`, `ExecucaoCapturaRow`, `DigestLogRow`.
  - `def make_session(database_url) -> sessionmaker`.
  - `def upsert_editais(session, editais_com_score: list[tuple[Edital, ScoreRelevancia, str]]) -> tuple[int, int]` — `(novos, atualizados)`; índice único `(fonte, chave_natural)`; `hash_conteudo` decide atualização; grava score/motivo/status=novo.
  - `def registar_execucao(session, fonte, inicio, fim, lidos, novos, relevantes, status, erro="", iniciado=None, terminado=None) -> None`.
  - `def ultima_captura(session, fonte) -> datetime | None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/db/test_repo.py
import os
from datetime import date
from decimal import Decimal
import pytest
from app.domain.edital import Edital, Fonte
from app.domain.relevancia import ScoreRelevancia
from app.domain.dedup import hash_conteudo
from app.db.engine import make_session
from app.db import repo

pytestmark = pytest.mark.skipif(not os.getenv("MYLIC_DATABASE_URL"), reason="sem Postgres")


def _ed(chave, objeto="clipping"):
    return Edital(Fonte.PNCP, chave, objeto, "Org", "00000000000191", "AM", "Manaus",
                  "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")


def test_upsert_nao_duplica_e_conta():
    Session = make_session(os.environ["MYLIC_DATABASE_URL"])
    with Session() as s:
        e = _ed("k-upsert-1")
        sc = ScoreRelevancia(0.5, ("clipping",))
        novos, atual = repo.upsert_editais(s, [(e, sc, hash_conteudo(e))])
        s.commit()
        assert (novos, atual) == (1, 0)
        novos2, _ = repo.upsert_editais(s, [(e, sc, hash_conteudo(e))])
        s.commit()
        assert novos2 == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker compose up -d postgres && export MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5432/mylic && uv run pytest tests/db/test_repo.py -v`
Expected: FAIL (tabela inexistente / módulo em falta).

- [ ] **Step 3: Write minimal implementation**

```python
# app/db/base.py
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

```python
# app/db/models.py
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, DateTime, Date, Float, ForeignKey, UniqueConstraint, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class EditalRow(Base):
    __tablename__ = "edital"
    __table_args__ = (UniqueConstraint("fonte", "chave_natural", name="uq_edital_fonte_chave"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String(20), index=True)
    chave_natural: Mapped[str] = mapped_column(String(200))
    hash_conteudo: Mapped[str] = mapped_column(String(64))
    objeto: Mapped[str] = mapped_column(Text)
    orgao_nome: Mapped[str] = mapped_column(String(300), default="")
    orgao_cnpj: Mapped[str] = mapped_column(String(20), default="")
    uf: Mapped[str | None] = mapped_column(String(2))
    municipio: Mapped[str | None] = mapped_column(String(200))
    modalidade: Mapped[str | None] = mapped_column(String(120))
    valor_estimado: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    data_publicacao: Mapped[datetime | None] = mapped_column(Date, index=True)
    data_abertura: Mapped[datetime | None] = mapped_column(Date)
    data_fim_propostas: Mapped[datetime | None] = mapped_column(Date)
    score_relevancia: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    motivo_relevancia: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="novo", index=True)
    url_origem: Mapped[str] = mapped_column(Text, default="")
    capturado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    arquivos: Mapped[list["ArquivoEditalRow"]] = relationship(
        back_populates="edital", cascade="all, delete-orphan")


class ArquivoEditalRow(Base):
    __tablename__ = "arquivo_edital"
    id: Mapped[int] = mapped_column(primary_key=True)
    edital_id: Mapped[int] = mapped_column(ForeignKey("edital.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20))
    caminho_local: Mapped[str] = mapped_column(Text)
    hash: Mapped[str] = mapped_column(String(64), default="")
    baixado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    edital: Mapped[EditalRow] = relationship(back_populates="arquivos")


class ProjetoInteresseRow(Base):
    __tablename__ = "projeto_interesse"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    palavras_chave: Mapped[list] = mapped_column(JSON, default=list)
    filtros: Mapped[dict] = mapped_column(JSON, default=dict)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExecucaoCapturaRow(Base):
    __tablename__ = "execucao_captura"
    id: Mapped[int] = mapped_column(primary_key=True)
    fonte: Mapped[str] = mapped_column(String(20), index=True)
    janela_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    janela_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_lidos: Mapped[int] = mapped_column(default=0)
    total_novos: Mapped[int] = mapped_column(default=0)
    total_relevantes: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="sucesso")
    erro: Mapped[str] = mapped_column(Text, default="")
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    terminado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DigestLogRow(Base):
    __tablename__ = "digest_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    data_ref: Mapped[datetime] = mapped_column(Date, index=True)
    canais: Mapped[str] = mapped_column(String(120), default="")
    enviado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resumo: Mapped[dict] = mapped_column(JSON, default=dict)
```

```python
# app/db/engine.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def make_session(database_url: str) -> sessionmaker:
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, future=True)
```

```python
# app/db/repo.py
from datetime import datetime, timezone
from sqlalchemy import select
from app.domain.edital import Edital
from app.domain.relevancia import ScoreRelevancia
from app.db.models import EditalRow, ExecucaoCapturaRow


def upsert_editais(session, editais_com_score: list[tuple[Edital, ScoreRelevancia, str]]) -> tuple[int, int]:
    novos = atualizados = 0
    for e, sc, h in editais_com_score:
        row = session.scalar(select(EditalRow).where(
            EditalRow.fonte == e.fonte.value, EditalRow.chave_natural == e.chave_natural))
        if row is None:
            session.add(EditalRow(
                fonte=e.fonte.value, chave_natural=e.chave_natural, hash_conteudo=h,
                objeto=e.objeto, orgao_nome=e.orgao_nome, orgao_cnpj=e.orgao_cnpj,
                uf=e.uf, municipio=e.municipio, modalidade=e.modalidade,
                valor_estimado=e.valor_estimado, data_publicacao=e.data_publicacao,
                data_abertura=e.data_abertura, data_fim_propostas=e.data_fim_propostas,
                score_relevancia=sc.valor, motivo_relevancia=",".join(sc.termos),
                status="novo", url_origem=e.url_origem,
                capturado_em=datetime.now(timezone.utc)))
            novos += 1
        elif row.hash_conteudo != h:
            row.hash_conteudo = h
            row.objeto = e.objeto
            row.score_relevancia = sc.valor
            row.motivo_relevancia = ",".join(sc.termos)
            atualizados += 1
    return novos, atualizados


def registar_execucao(session, fonte, inicio, fim, lidos, novos, relevantes, status, erro="", iniciado=None, terminado=None):
    agora = datetime.now(timezone.utc)
    session.add(ExecucaoCapturaRow(
        fonte=fonte, janela_inicio=inicio, janela_fim=fim, total_lidos=lidos,
        total_novos=novos, total_relevantes=relevantes, status=status, erro=erro,
        iniciado_em=iniciado or agora, terminado_em=terminado or agora))


def ultima_captura(session, fonte) -> datetime | None:
    return session.scalar(select(ExecucaoCapturaRow.janela_fim)
                          .where(ExecucaoCapturaRow.fonte == fonte, ExecucaoCapturaRow.status != "falha")
                          .order_by(ExecucaoCapturaRow.janela_fim.desc()).limit(1))
```

Alembic: `uv run alembic init alembic`; apontar `alembic/env.py` para `app.db.base.Base.metadata` (importando `app.db.models`) e ler `MYLIC_DATABASE_URL`; gerar `uv run alembic revision --autogenerate -m "inicial edital"` e **renomear** o revision id para `inicial_edital_20260910` (id descritivo, não sequencial — lição LexFlow).

- [ ] **Step 4: Run migração + test**

Run: `uv run alembic upgrade head && uv run pytest tests/db/test_repo.py -v`
Expected: migração aplica; test PASS.

- [ ] **Step 5: Commit**

```bash
git add app/db alembic alembic.ini tests/db/test_repo.py
git commit -m "feat(db): modelos, repositorio upsert/execucao e migracao inicial"
```

---

### Task 12: Canais de digest — e-mail, Telegram e registo de página

**Files:**
- Create: `app/adapters/notificacao/render.py`, `app/adapters/notificacao/email.py`, `app/adapters/notificacao/telegram.py`, `app/adapters/notificacao/portal.py`, `app/adapters/notificacao/__init__.py`
- Test: `tests/adapters/test_notificacao.py`

**Interfaces:**
- Consumes: `Digest`, `DigestLogRow`, `make_client`.
- Produces:
  - `def render_html(d: Digest) -> str` e `def render_texto(d: Digest) -> str`.
  - `class EmailDigest(host, port, user, password, remetente, destinatario)` — `enviar(d)` via `smtplib.SMTP` + `starttls`.
  - `class TelegramDigest(bot_token, chat_id, client_factory=make_client)` — `enviar(d)` POST `/bot{token}/sendMessage`.
  - `class PortalDigest(session_factory)` — `enviar(d)` grava `DigestLogRow`.

- [ ] **Step 1: Write the failing test**

```python
# tests/adapters/test_notificacao.py
from datetime import date
from app.domain.digest import Digest
from app.adapters.notificacao.render import render_html, render_texto
from app.adapters.notificacao.telegram import TelegramDigest


def _digest():
    return Digest(date(2026, 9, 1), 40, 3, 3, ("compras_gov",), (), ())


def test_render_html_tem_totais():
    html = render_html(_digest())
    assert "40" in html and "compras_gov" in html


def test_render_texto_nao_quebra_sem_destaques():
    txt = render_texto(_digest())
    assert "Radar de Editais" in txt


def test_telegram_faz_post():
    chamadas = {}

    class FakeResp:
        status_code = 200
        def raise_for_status(self): pass

    class FakeClient:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def post(self, url, json):
            chamadas["url"] = url
            chamadas["json"] = json
            return FakeResp()

    tg = TelegramDigest("TOKEN", "123", client_factory=lambda base: FakeClient())
    tg.enviar(_digest())
    assert "/botTOKEN/sendMessage" in chamadas["url"]
    assert chamadas["json"]["chat_id"] == "123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/adapters/test_notificacao.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/adapters/notificacao/render.py
from app.domain.digest import Digest


def render_texto(d: Digest) -> str:
    linhas = [f"Radar de Editais — {d.data_ref.isoformat()}",
              f"Novos: {d.total_novos} | Relevantes: {d.total_relevantes} | Downloads: {d.total_downloads}"]
    if d.fontes_com_falha:
        linhas.append(f"Fontes com falha: {', '.join(d.fontes_com_falha)}")
    for p in d.projetos:
        linhas.append(f"Projeto {p.nome}: {p.novos} novos, {p.prazo_a_fechar} com prazo a fechar")
    for e in d.destaques:
        linhas.append(f"- {e.objeto[:90]} ({e.orgao_nome})")
    return "\n".join(linhas)


def render_html(d: Digest) -> str:
    itens = "".join(f"<li>{e.objeto[:120]} — <b>{e.orgao_nome}</b> ({e.uf or ''})</li>" for e in d.destaques)
    projetos = "".join(f"<li>{p.nome}: {p.novos} novos, {p.prazo_a_fechar} a fechar</li>" for p in d.projetos)
    falha = f"<p>Fontes com falha: {', '.join(d.fontes_com_falha)}</p>" if d.fontes_com_falha else ""
    return (f"<h2>Radar de Editais — {d.data_ref.isoformat()}</h2>"
            f"<p>Novos: {d.total_novos} | Relevantes: {d.total_relevantes} | Downloads: {d.total_downloads}</p>"
            f"{falha}<h3>Projetos</h3><ul>{projetos}</ul><h3>Destaques</h3><ul>{itens}</ul>")
```

```python
# app/adapters/notificacao/telegram.py
from app.domain.digest import Digest
from app.adapters.http_client import make_client
from app.adapters.notificacao.render import render_texto


class TelegramDigest:
    def __init__(self, bot_token: str, chat_id: str, client_factory=make_client) -> None:
        self._token = bot_token
        self._chat = chat_id
        self._cf = client_factory

    def enviar(self, d: Digest) -> None:
        with self._cf("https://api.telegram.org") as c:
            r = c.post(f"/bot{self._token}/sendMessage",
                       json={"chat_id": self._chat, "text": render_texto(d)[:4000]})
            r.raise_for_status()
```

```python
# app/adapters/notificacao/email.py
import smtplib
from email.message import EmailMessage
from app.domain.digest import Digest
from app.adapters.notificacao.render import render_html, render_texto


class EmailDigest:
    def __init__(self, host, port, user, password, remetente, destinatario) -> None:
        self._host, self._port = host, port
        self._user, self._password = user, password
        self._de, self._para = remetente, destinatario

    def enviar(self, d: Digest) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"Radar de Editais — {d.data_ref.isoformat()}"
        msg["From"] = self._de
        msg["To"] = self._para
        msg.set_content(render_texto(d))
        msg.add_alternative(render_html(d), subtype="html")
        with smtplib.SMTP(self._host, self._port) as s:
            s.starttls()
            if self._user:
                s.login(self._user, self._password)
            s.send_message(msg)
```

```python
# app/adapters/notificacao/portal.py
from datetime import datetime, timezone
from app.domain.digest import Digest
from app.db.models import DigestLogRow


class PortalDigest:
    def __init__(self, session_factory) -> None:
        self._sf = session_factory

    def enviar(self, d: Digest) -> None:
        with self._sf() as s:
            s.add(DigestLogRow(
                data_ref=d.data_ref, canais="portal",
                enviado_em=datetime.now(timezone.utc),
                resumo={"novos": d.total_novos, "relevantes": d.total_relevantes,
                        "downloads": d.total_downloads,
                        "fontes_com_falha": list(d.fontes_com_falha)}))
            s.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/adapters/test_notificacao.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add app/adapters/notificacao tests/adapters/test_notificacao.py
git commit -m "feat(adapters): canais de digest (email, telegram, portal) + render"
```

---

### Task 13: Orquestrador `run_daily` (isolamento por fonte + janela incremental)

**Files:**
- Create: `app/scheduler/__init__.py`, `app/scheduler/orquestrador.py`, `app/scheduler/run_daily.py`
- Test: `tests/scheduler/test_orquestrador.py`

**Interfaces:**
- Consumes: portas; `deduplicar`, `hash_conteudo`, `montar_digest`; `repo.upsert_editais`, `repo.registar_execucao`, `repo.ultima_captura`.
- Produces:
  - `@dataclass class Resultado: novos:int=0; relevantes:int=0; downloads:int=0; fontes_falha:list[str]=field(default_factory=list)`
  - `def executar(session, fontes, classificador, armazenamento, canais, baixar_conteudo, inicio, fim, score_piso) -> Resultado`
  - `def main() -> None` em `run_daily.py`.

- [ ] **Step 1: Write the failing test**

```python
# tests/scheduler/test_orquestrador.py
from datetime import date
from decimal import Decimal
from app.domain.edital import Edital, Fonte, ArquivoRef, TipoArquivo
from app.domain.relevancia import ScoreRelevancia


class FonteFake:
    def __init__(self, nome, editais, explode=False):
        self.nome = nome
        self._e = editais
        self._explode = explode
    def buscar(self, inicio, fim):
        if self._explode:
            raise RuntimeError("fonte caiu")
        return self._e
    def listar_arquivos(self, e):
        return [ArquivoRef(TipoArquivo.EDITAL, "http://x/edital.pdf", "edital.pdf")]


class ClassifFake:
    def classificar(self, e):
        rel = "clipping" in e.objeto
        return ScoreRelevancia(0.9 if rel else 0.0, ("clipping",) if rel else ())


class StoreFake:
    def __init__(self): self.guardados = []
    def guardar(self, e, arq, conteudo): self.guardados.append(e.chave_natural); return "/tmp/x.pdf"


class CanalFake:
    def __init__(self): self.enviados = []
    def enviar(self, d): self.enviados.append(d)


class SessionFake:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def add(self, *a): pass
    def commit(self): pass
    def scalar(self, *a, **k): return None


def _ed(fonte, chave, objeto):
    return Edital(fonte, chave, objeto, "Org", "00000000000191", "AM", "Manaus",
                  "Pregao", Decimal("1"), date(2026, 9, 1), None, None, "http://x")


def test_fonte_que_cai_nao_derruba_a_outra(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (len(itens), 0))
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)
    boa = FonteFake("pncp", [_ed(Fonte.PNCP, "k1", "servico de clipping")])
    ma = FonteFake("compras_gov", [], explode=True)
    store, canal = StoreFake(), CanalFake()
    res = orq.executar(SessionFake(), [boa, ma], ClassifFake(), store, [canal],
                       baixar_conteudo=lambda url: b"%PDF", inicio=date(2026, 9, 1),
                       fim=date(2026, 9, 2), score_piso=0.34)
    assert "compras_gov" in res.fontes_falha
    assert res.novos == 1
    assert store.guardados == ["k1"]
    assert len(canal.enviados) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/scheduler/test_orquestrador.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/scheduler/orquestrador.py
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from app.domain.dedup import deduplicar, hash_conteudo
from app.domain.digest import montar_digest
from app.db.repo import upsert_editais, registar_execucao


@dataclass
class Resultado:
    novos: int = 0
    relevantes: int = 0
    downloads: int = 0
    fontes_falha: list[str] = field(default_factory=list)


def executar(session, fontes, classificador, armazenamento, canais,
             baixar_conteudo: Callable[[str], bytes], inicio: date, fim: date,
             score_piso: float) -> Resultado:
    res = Resultado()
    capturados = []
    por_nome = {}
    for f in fontes:
        try:
            editais = f.buscar(inicio, fim)
            capturados.extend(editais)
            por_nome[f.nome] = f
            registar_execucao(session, f.nome, inicio, fim, len(editais), 0, 0, "sucesso")
        except Exception as exc:  # isolamento por fonte
            res.fontes_falha.append(f.nome)
            registar_execucao(session, f.nome, inicio, fim, 0, 0, 0, "falha", str(exc))
    session.commit()

    editais = deduplicar(capturados)
    com_score = [(e, classificador.classificar(e), hash_conteudo(e)) for e in editais]
    res.novos, _ = upsert_editais(session, com_score)
    session.commit()

    relevantes = [e for e, sc, _ in com_score if sc.valor >= score_piso]
    res.relevantes = len(relevantes)
    for e in relevantes:
        fonte = por_nome.get(e.fonte.value)
        if fonte is None:
            continue
        for arq in fonte.listar_arquivos(e):
            if not arq.url:
                continue
            try:
                armazenamento.guardar(e, arq, baixar_conteudo(arq.url))
                res.downloads += 1
            except Exception:
                pass  # PDF que falha nao bloqueia o edital

    digest = montar_digest(fim, relevantes, res.novos, res.downloads, res.fontes_falha, [])
    for canal in canais:
        canal.enviar(digest)
    return res
```

```python
# app/scheduler/run_daily.py
from datetime import date, timedelta
from app.config import Settings
from app.db.engine import make_session
from app.db.repo import ultima_captura
from app.domain.lexico import LEXICO_TIPO_LEXFLOW
from app.adapters.classificador.keyword import KeywordClassificador
from app.adapters.fontes.pncp import FontePncp
from app.adapters.fontes.compras_gov import FonteComprasGov
from app.adapters.armazenamento.disco import ArmazenamentoDisco
from app.adapters.notificacao.telegram import TelegramDigest
from app.adapters.notificacao.email import EmailDigest
from app.adapters.notificacao.portal import PortalDigest
from app.adapters.http_client import make_client
from app.scheduler.orquestrador import executar


def main() -> None:
    s = Settings()
    Session = make_session(s.database_url)
    with Session() as sess:
        uc = ultima_captura(sess, "pncp")
    inicio = uc.date() if uc else date.today() - timedelta(days=s.janela_inicial_dias)
    fim = date.today()
    fontes = [FontePncp(s.pncp_base_url), FonteComprasGov(s.compras_base_url)]
    canais = [PortalDigest(Session)]
    if s.telegram_bot_token and s.telegram_chat_id:
        canais.append(TelegramDigest(s.telegram_bot_token, s.telegram_chat_id))
    if s.smtp_host and s.smtp_to:
        canais.append(EmailDigest(s.smtp_host, s.smtp_port, s.smtp_user, s.smtp_password, s.smtp_from, s.smtp_to))

    def baixar(url: str) -> bytes:
        with make_client("") as c:
            r = c.get(url)
            r.raise_for_status()
            return r.content

    with Session() as sess:
        res = executar(sess, fontes, KeywordClassificador(LEXICO_TIPO_LEXFLOW),
                       ArmazenamentoDisco(s.pdf_dir), canais, baixar, inicio, fim, s.score_piso)
    print(f"novos={res.novos} relevantes={res.relevantes} downloads={res.downloads} "
          f"fontes_falha={res.fontes_falha}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/scheduler/test_orquestrador.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/scheduler tests/scheduler/test_orquestrador.py
git commit -m "feat(scheduler): orquestrador run_daily com isolamento por fonte e janela incremental"
```

---

### Task 14: E2E — fake ao nível do fio (PNCP) + captura→digest

**Files:**
- Create: `tests/e2e/__init__.py`, `tests/e2e/fake_portais.py`, `tests/e2e/test_captura_ate_digest.py`
- Test: `tests/e2e/test_captura_ate_digest.py`

**Interfaces:**
- Consumes: `executar`, `FontePncp` apontada ao fake, `KeywordClassificador`.
- Produces: servidor HTTP (stdlib `http.server` em thread) que serve `/v1/contratacoes/publicacao` (paginado) e `/v1/orgaos/.../arquivos`; o teste aponta `FontePncp(base_url=fake)` e verifica caixa populada + digest. **Sem monkeypatch do nosso código de rede** — o fake fala HTTP real; o único monkeypatch é do `upsert_editais`/`registar_execucao` para não exigir Postgres neste teste.

- [ ] **Step 1: Write the failing test**

```python
# tests/e2e/test_captura_ate_digest.py
from datetime import date
from tests.e2e.fake_portais import servidor_fake
from app.adapters.fontes.pncp import FontePncp
from app.adapters.classificador.keyword import KeywordClassificador
from app.domain.lexico import LEXICO_TIPO_LEXFLOW


class StoreFake:
    def __init__(self): self.n = 0
    def guardar(self, e, arq, conteudo): self.n += 1; return "/tmp/x.pdf"


class CanalFake:
    def __init__(self): self.enviados = []
    def enviar(self, d): self.enviados.append(d)


class SessionFake:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def add(self, *a): pass
    def commit(self): pass
    def scalar(self, *a, **k): return None


def test_captura_ate_digest(monkeypatch):
    import app.scheduler.orquestrador as orq
    monkeypatch.setattr(orq, "upsert_editais", lambda s, itens: (len(itens), 0))
    monkeypatch.setattr(orq, "registar_execucao", lambda *a, **k: None)
    with servidor_fake() as base_url:
        fonte = FontePncp(base_url)
        store, canal = StoreFake(), CanalFake()
        res = orq.executar(SessionFake(), [fonte], KeywordClassificador(LEXICO_TIPO_LEXFLOW),
                           store, [canal], baixar_conteudo=lambda url: b"%PDF",
                           inicio=date(2026, 9, 1), fim=date(2026, 9, 2), score_piso=0.05)
    assert res.novos >= 1
    assert res.relevantes >= 1
    assert store.n >= 1
    assert len(canal.enviados) == 1
    print(f"E2E cenarios: novos={res.novos} relevantes={res.relevantes} downloads={store.n}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/e2e/test_captura_ate_digest.py -v`
Expected: FAIL (`fake_portais` inexistente).

- [ ] **Step 3: Write the wire-level fake**

```python
# tests/e2e/fake_portais.py
import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

_EDITAL = {
    "orgaoEntidade": {"cnpj": "00000000000191", "razaoSocial": "Tribunal X"},
    "unidadeOrgao": {"ufSigla": "AM", "municipioNome": "Manaus"},
    "anoCompra": 2026, "sequencialCompra": 42,
    "objetoCompra": "Contratacao de servico de clipping e monitoramento de publicacoes",
    "modalidadeNome": "Pregao", "valorTotalEstimado": 1000.0,
    "dataPublicacaoPncp": "2026-09-01T10:00:00",
}


class _H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if "/v1/contratacoes/publicacao" in self.path:
            body = {"data": [_EDITAL], "totalPaginas": 1, "totalRegistros": 1, "numeroPagina": 1}
        elif "/arquivos" in self.path:
            body = [{"url": "http://x/edital.pdf", "titulo": "Edital.pdf"}]
        else:
            self.send_response(404); self.end_headers(); return
        data = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)


@contextlib.contextmanager
def servidor_fake():
    srv = HTTPServer(("127.0.0.1", 0), _H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/e2e/test_captura_ate_digest.py -v -s`
Expected: PASS; imprime `E2E cenarios: ...` (piso declarado, > 0).

- [ ] **Step 5: Commit**

```bash
git add tests/e2e
git commit -m "test(e2e): fake ao nivel do fio (PNCP) validando captura ate digest"
```

---

## Self-Review (executado ao escrever o plano)

**1. Spec coverage:** Fundações/hexagonal/import-linter → Task 1, 6. Domínio (Edital, relevância, dedup, digest) → Tasks 2-5. Portas → Task 6. TLS/retry → Task 7. PNCP (busca+arquivos) → Task 8. Compras.gov → Task 9. Armazenamento disco → Task 10. Persistência+Alembic+FK ON DELETE → Task 11. Digest 3 canais → Task 12. Scheduler incremental + isolamento por fonte + piso → Task 13. E2E fake ao nível do fio → Task 14.
- **Lacuna consciente:** a **caixa Next.js**, a **API FastAPI** e a **UI de projetos de interesse** ficam para o **Plano 1B** (portal), que lê a BD que este plano enche. `projeto_interesse` já tem tabela (Task 11) e o digest aceita `LinhaProjeto` (Task 5), mas o cálculo das linhas de projeto entra no 1B/Fase 2 — a Task 13 chama `montar_digest(..., [])` e isso está explícito.
- **Questões em aberto do PRD** (léxico, piso, modalidades, dedup entre fontes) ficam com valores iniciais (léxico Task 3, piso 0.34 na config, `MODALIDADES` Task 8, dedup Task 4), a calibrar com dados reais.

**2. Placeholder scan:** sem "TBD/TODO"; o único ponto "ajustar aos campos reais" (Tasks 8-9) é **deliberado e instruído** (capturar fixture primeiro), não código em falta.

**3. Type consistency:** `Edital`, `ScoreRelevancia(valor, termos)`, `Fonte`, `ArquivoRef(tipo,url,nome)`, `Digest`, `LinhaProjeto`, portas e `Resultado` consistentes entre Tasks 2→14. `render_texto` corrigido para não chamar método inexistente em `Edital`.

## Nota de execução

Tasks 8, 9 e 11 exigem **rede** (capturar fixtures do PNCP/Compras) e **Postgres**
(docker). Se num passo a rede pública falhar, capturar o fixture depois e manter o
teste com `skip` de razão explícita até o fixture existir — nunca inventar o JSON.
