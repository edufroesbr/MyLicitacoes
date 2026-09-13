# Fase 1B-B — Frontend Next.js (caixa/digest/projetos) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A caixa estilo e-mail em Next.js que consome a API 1B-A: listar/filtrar/buscar editais, ver detalhe + PDF, mudar status, ver o digest do dia, e gerir projetos de interesse. Visual coerente com o LexFlow (tokens copiados), zero dependencia do repo Lex_Flow.

**Architecture:** Next.js App Router + TypeScript + Tailwind. Componentes client simples (`useState`+`fetch`), sem biblioteca de estado nem UI kit. Fala com a API local (`http://localhost:8000`) via um cliente tipado em `lib/api.ts`. E2E real com Playwright (chromium) sobre a stack em pe.

**Tech Stack:** Node 20, Next.js 14 (App Router), TypeScript, Tailwind CSS, Playwright.

**Spec:** [`docs/superpowers/specs/2026-09-10-radar-editais-lexflow-design.md`](../specs/2026-09-10-radar-editais-lexflow-design.md) §8; API em [`2026-09-13-fase1b-backend-api.md`](2026-09-13-fase1b-backend-api.md).

## Global Constraints

- **Repo:** `C:\Users\edufr\.gemini\antigravity-ide\scratch\MyLicitacoes`, pasta `frontend/`. Branch definida pelo controlador SDD.
- **A API 1B-A tem de existir e estar verde antes deste plano** (endpoints `/editais`, `/editais/{id}`, `PATCH`, `/editais/{id}/arquivo/{aid}`, `/digest/hoje`, `/projetos-interesse`).
- Base URL da API por env: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- Ponytail: sem Redux/Zustand/React-Query, sem component library. `fetch` nativo, `useState`/`useEffect`, elementos de formulario nativos.
- Windows/Git Bash; gate Fact-Forcing (fatos antes do 1.o Bash e de cada Write/Edit novo; repetir). pt-BR na UI, ASCII no codigo.
- **E2E e a camada que decide** (design §10): Playwright real contra a stack (Postgres + uvicorn + next dev), nao mocks.

---

### Task 1: Scaffold Next.js + Tailwind + tokens do LexFlow + base da API

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/next.config.mjs`, `frontend/tailwind.config.ts`, `frontend/postcss.config.mjs`, `frontend/app/globals.css`, `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/.env.local.example`, `frontend/lib/config.ts`

**Interfaces:**
- Produces: app Next.js que arranca (`npm run dev`) e faz build (`npm run build`); `lib/config.ts` exporta `API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"`; `app/page.tsx` liga para `/caixa`.
- Tokens: cores e stack de fontes **copiados** do LexFlow.

- [ ] **Step 1: Scaffold**

Cria o app manualmente (evita o wizard interativo do create-next-app). `frontend/package.json`:
```json
{
  "name": "mylicitacoes-frontend",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "next": "14.2.5",
    "react": "18.3.1",
    "react-dom": "18.3.1"
  },
  "devDependencies": {
    "@playwright/test": "1.46.0",
    "@types/node": "20.14.0",
    "@types/react": "18.3.0",
    "autoprefixer": "10.4.19",
    "postcss": "8.4.39",
    "tailwindcss": "3.4.7",
    "typescript": "5.5.4"
  }
}
```

`frontend/lib/config.ts`:
```ts
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
```

`frontend/.env.local.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Cria `tsconfig.json` (Next default), `next.config.mjs` (`export default {}`), `postcss.config.mjs` (tailwind+autoprefixer), `tailwind.config.ts` (content: `app/**`, `components/**`), `app/globals.css` (`@tailwind base/components/utilities`), `app/layout.tsx` (html/body + globals.css + lang="pt-BR"), `app/page.tsx` (link para `/caixa`).

- [ ] **Step 2: Copiar os tokens do LexFlow**

Le o `tailwind.config.*` e o `globals.css` do frontend do LexFlow em `C:\Users\edufr\.gemini\antigravity-ide\scratch\Lex_Flow\frontend\` e **copia para dentro** deste `tailwind.config.ts`/`globals.css`: a paleta de cores (theme.extend.colors), a stack de fontes e os raios/spacing custom. Copia valores, NAO importes nem referencies ficheiros do Lex_Flow (o repo fica isolado). Se o LexFlow usar CSS variables no globals, copia as `:root { --... }` relevantes.
> **Ruling do implementador:** se o design system do LexFlow for grande, copia so os tokens efetivamente usados pela caixa (cores de fundo/superficie/texto/acento, fonte, radius). YAGNI no resto.

- [ ] **Step 3: Verificar build**

Run: `cd "C:/Users/edufr/.gemini/antigravity-ide/scratch/MyLicitacoes/frontend" && npm install && npm run build`
Expected: build passa (app minima).

- [ ] **Step 4: Commit**

```bash
git add frontend
git commit -m "chore(frontend): scaffold Next.js + Tailwind com tokens do LexFlow"
```

---

### Task 2: Cliente da API tipado (`lib/api.ts`)

**Files:**
- Create: `frontend/lib/api.ts`, `frontend/lib/types.ts`

**Interfaces:**
- Produces (em `types.ts`): `EditalResumo`, `EditalDetalhe`, `ArquivoResumo`, `Pagina<T>`, `Projeto`, `StatusCaixa`.
- Produces (em `api.ts`): `listarEditais`, `obterEdital`, `mudarStatus`, `urlArquivo`, `digestHoje`, `listarProjetos`, `criarProjeto`, `atualizarProjeto`, `apagarProjeto`.

- [ ] **Step 1: Implement**

```ts
// frontend/lib/types.ts
export type StatusCaixa = "novo" | "lido" | "arquivado" | "oportunidade";

export interface EditalResumo {
  id: number; fonte: string; objeto: string; orgao_nome: string;
  uf: string | null; modalidade: string | null; valor_estimado: string | null;
  data_publicacao: string | null; data_fim_propostas: string | null;
  score_relevancia: number; status: StatusCaixa;
}
export interface ArquivoResumo { id: number; tipo: string; }
export interface EditalDetalhe extends EditalResumo {
  orgao_cnpj: string; municipio: string | null; motivo_relevancia: string;
  url_origem: string; arquivos: ArquivoResumo[];
}
export interface Pagina<T> { itens: T[]; total: number; pagina: number; tamanho: number; }
export interface Projeto {
  id: number; nome: string; palavras_chave: string[]; filtros: Record<string, unknown>;
  ativo: boolean; criado_em: string;
}
```

```ts
// frontend/lib/api.ts
import { API_URL } from "./config";
import type { EditalResumo, EditalDetalhe, Pagina, Projeto, StatusCaixa } from "./types";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json() as Promise<T>;
}

export interface FiltrosEditais {
  uf?: string; modalidade?: string; fonte?: string; status?: string;
  score_min?: number; q?: string; projeto_id?: number; pagina?: number; tamanho?: number;
}

export async function listarEditais(f: FiltrosEditais = {}): Promise<Pagina<EditalResumo>> {
  const qs = new URLSearchParams();
  Object.entries(f).forEach(([k, v]) => { if (v !== undefined && v !== "") qs.set(k, String(v)); });
  return j(await fetch(`${API_URL}/editais?${qs}`, { cache: "no-store" }));
}
export async function obterEdital(id: number): Promise<EditalDetalhe> {
  return j(await fetch(`${API_URL}/editais/${id}`, { cache: "no-store" }));
}
export async function mudarStatus(id: number, status: StatusCaixa): Promise<EditalDetalhe> {
  return j(await fetch(`${API_URL}/editais/${id}`, {
    method: "PATCH", headers: { "content-type": "application/json" },
    body: JSON.stringify({ status }) }));
}
export function urlArquivo(editalId: number, arquivoId: number): string {
  return `${API_URL}/editais/${editalId}/arquivo/${arquivoId}`;
}
export async function digestHoje() {
  return j<{ data_ref: string; resumo: any; destaques: EditalResumo[] }>(
    await fetch(`${API_URL}/digest/hoje`, { cache: "no-store" }));
}
export async function listarProjetos(): Promise<Projeto[]> {
  return j(await fetch(`${API_URL}/projetos-interesse`, { cache: "no-store" }));
}
export async function criarProjeto(p: Partial<Projeto>): Promise<Projeto> {
  return j(await fetch(`${API_URL}/projetos-interesse`, {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(p) }));
}
export async function atualizarProjeto(id: number, p: Partial<Projeto>): Promise<Projeto> {
  return j(await fetch(`${API_URL}/projetos-interesse/${id}`, {
    method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify(p) }));
}
export async function apagarProjeto(id: number): Promise<void> {
  const r = await fetch(`${API_URL}/projetos-interesse/${id}`, { method: "DELETE" });
  if (!r.ok) throw new Error(`API ${r.status}`);
}
```

- [ ] **Step 2: Verify build** — `cd frontend && npm run build` sem erros de tipo.

- [ ] **Step 3: Commit**

```bash
git add frontend/lib
git commit -m "feat(frontend): cliente tipado da API + tipos"
```

---

### Task 3: Caixa (lista) — `app/caixa/page.tsx`

**Files:**
- Create: `frontend/app/caixa/page.tsx`, `frontend/components/Badge.tsx`, `frontend/components/Filtros.tsx`
- Test: coberto pelo E2E (Task 7)

**Interfaces:**
- Consumes: `listarEditais`, `EditalResumo`.
- Produces: pagina client que lista editais (nao-lidos em destaque, badge de score e de prazo), filtros (uf/modalidade/fonte/status/score_min/q) ligados ao estado, paginacao, cada linha liga a `/editais/{id}`.

- [ ] **Step 1: Implement**

`components/Badge.tsx`: colore por score (`>=0.67` acento forte, `>=0.34` medio) + badge de prazo (dias ate `data_fim_propostas`, vermelho se <=3).

`components/Filtros.tsx`: `<select>`/`<input>` nativos (uf, modalidade, fonte, status, score_min, busca `q`); chama `onChange(filtros)`.

`app/caixa/page.tsx` (`"use client"`): `useState` dos filtros + pagina; `useEffect` chama `listarEditais`; `<ul>` de linhas com objeto (truncado), orgao, uf, modalidade, valor, data, badges; nao-lidos (`status==="novo"`) em realce; paginacao via `total`/`tamanho`; `<Link href={/editais/${id}}>`. Estado de loading/erro por texto simples.

- [ ] **Step 2: Verify build** — passa.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/caixa frontend/components/Badge.tsx frontend/components/Filtros.tsx
git commit -m "feat(frontend): caixa (lista + filtros + paginacao + badges)"
```

---

### Task 4: Detalhe do edital — `app/editais/[id]/page.tsx`

**Files:**
- Create: `frontend/app/editais/[id]/page.tsx`, `frontend/components/AcoesStatus.tsx`
- Test: E2E (Task 7)

**Interfaces:**
- Consumes: `obterEdital`, `mudarStatus`, `urlArquivo`.
- Produces: detalhe (client) com metadados (objeto completo, orgao+cnpj, uf/municipio, modalidade, valor, datas, `motivo_relevancia`, link `url_origem`), lista de `arquivos` com link para `urlArquivo(id, arquivoId)`, e `AcoesStatus` (ler/arquivar/oportunidade -> `mudarStatus` + atualiza estado local).

- [ ] **Step 1: Implement**

`components/AcoesStatus.tsx`: recebe `editalId`, `statusAtual`, `onMudou(novo)`; 3 botoes que chamam `mudarStatus`.

`app/editais/[id]/page.tsx` (`"use client"`, `params.id`): `useEffect` `obterEdital`; render dos campos; `<a href={urlArquivo(...)} target="_blank">` por arquivo; `<a href={url_origem} target="_blank">` para a origem; `AcoesStatus`.

- [ ] **Step 2: Verify build** — passa.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/editais frontend/components/AcoesStatus.tsx
git commit -m "feat(frontend): detalhe do edital (metadados + PDF + acoes)"
```

---

### Task 5: Digest do dia — `app/digest/page.tsx`

**Files:**
- Create: `frontend/app/digest/page.tsx`
- Test: E2E (Task 7)

**Interfaces:**
- Consumes: `digestHoje`.
- Produces: pagina com `data_ref`, `resumo` (novos/relevantes/downloads/fontes_com_falha) e lista de `destaques` (liga a `/editais/{id}`).

- [ ] **Step 1: Implement** — `"use client"`, `useEffect` `digestHoje`, cartoes de contadores + lista de destaques.

- [ ] **Step 2: Verify build** — passa.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/digest
git commit -m "feat(frontend): pagina do digest do dia"
```

---

### Task 6: Projetos de interesse (CRUD) — `app/projetos/page.tsx`

**Files:**
- Create: `frontend/app/projetos/page.tsx`, `frontend/components/ProjetoForm.tsx`
- Test: E2E (Task 7)

**Interfaces:**
- Consumes: `listarProjetos`, `criarProjeto`, `atualizarProjeto`, `apagarProjeto`.
- Produces: lista (nome, palavras-chave, ativo) com editar/apagar; `ProjetoForm` (nome, palavras-chave por virgula, filtros uf/modalidade, ativo) para criar/editar.

- [ ] **Step 1: Implement** — `"use client"`; estado da lista + formulario; palavras-chave: texto -> `split(",")` trim; filtros uf/modalidade `input`; guardar chama criar/atualizar e recarrega; apagar chama `apagarProjeto`. Um so componente de formulario para criar e editar, inline (sem modal library).

- [ ] **Step 2: Verify build** — passa.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/projetos frontend/components/ProjetoForm.tsx
git commit -m "feat(frontend): CRUD de projetos de interesse"
```

---

### Task 7: E2E Playwright sobre a stack real (a camada que decide)

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/e2e/caixa.spec.ts`, `scripts/seed_e2e.py`
- Test: `frontend/e2e/caixa.spec.ts`

**Interfaces:**
- Produces: teste Playwright que, com a stack em pe (Postgres + uvicorn + next dev), semeia >=1 edital relevante, abre `/caixa`, confirma que aparece, abre o detalhe, muda o status para "oportunidade" (persiste).

- [ ] **Step 1: Config + seed**

`playwright.config.ts`: `use.baseURL = "http://localhost:3000"`, chromium headless.

**Ruling do implementador:** o seed insere via `scripts/seed_e2e.py` (Python, reusa `app.db`) 1 edital relevante (objeto "servico de clipping ...", score 0.9, data_publicacao=hoje, status novo), idempotente por `chave_natural="e2e-seed"`. Evita um endpoint de escrita so-para-teste na API.

`scripts/seed_e2e.py`:
```python
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
```

- [ ] **Step 2: Write the E2E test**

```ts
// frontend/e2e/caixa.spec.ts
import { test, expect } from "@playwright/test";
import { execSync } from "node:child_process";

test.beforeAll(() => {
  execSync("uv run python scripts/seed_e2e.py", {
    cwd: "..", stdio: "inherit",
    env: { ...process.env, MYLIC_DATABASE_URL: process.env.MYLIC_DATABASE_URL! },
  });
});

test("caixa lista, abre detalhe e muda status", async ({ page }) => {
  await page.goto("/caixa");
  await expect(page.getByText(/clipping/i).first()).toBeVisible();
  await page.getByText(/clipping/i).first().click();
  await expect(page).toHaveURL(/\/editais\/\d+/);
  await page.getByRole("button", { name: /oportunidade/i }).click();
  await expect(page.getByText(/oportunidade/i).first()).toBeVisible();
});
```

- [ ] **Step 3: Run the E2E (stack em pe)**

```bash
cd "C:/Users/edufr/.gemini/antigravity-ide/scratch/MyLicitacoes" && docker compose up -d postgres
MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5433/mylic uv run alembic upgrade head
MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5433/mylic uv run uvicorn app.api.main:app --port 8000 &
cd frontend && npm run dev &
cd frontend && npx playwright install chromium && MYLIC_DATABASE_URL=postgresql+psycopg://mylic:mylic@localhost:5433/mylic npx playwright test
```
Expected: 1 passed. (Piso: falha se a caixa nao listar o edital semeado.)

- [ ] **Step 4: Commit**

```bash
git add frontend/playwright.config.ts frontend/e2e scripts/seed_e2e.py
git commit -m "test(e2e): Playwright sobre a stack real (caixa -> detalhe -> status)"
```

---

## Self-Review

**Spec coverage (design §8):** caixa+filtros+badges (T3), detalhe+PDF+acoes (T4), digest (T5), projetos CRUD (T6), tokens LexFlow (T1), cliente API (T2), E2E real (T7). Auth ausente (localhost).

**Placeholder scan:** sem TBD. Os dois pontos "derivados na implementacao" (copiar tokens do LexFlow T1; seed E2E T7) sao instrucoes deliberadas com ruling, nao codigo em falta.

**Type consistency:** `types.ts` espelha os schemas 1B-A (`EditalResumo`/`EditalDetalhe`/`Pagina`/`Projeto`/`StatusCaixa`); `api.ts` usa-os; as paginas consomem `api.ts`.

## Nota de execucao
Corre **depois** do 1B-A verde. O E2E (T7) exige a stack completa: **Docker/Postgres + uvicorn + next dev**. Sem eles, T1-T6 verificam-se por `npm run build`; so o T7 precisa da stack — e e o que decide.
