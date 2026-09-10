# MyLicitacoes — Radar de Editais tipo-LexFlow (Design)

> **Estado:** design aprovado em brainstorming (2026-09-10). Próximo passo:
> plano de implementação (`writing-plans`).
> **Fonte de verdade dos requisitos faseados:**
> [`docs/prd/radar-editais-lexflow/requirements.md`](../../prd/radar-editais-lexflow/requirements.md).

## 1. O que é (e o que não é)

**MyLicitacoes é um radar comercial / inteligência de mercado.** Um agente
autónomo captura, todos os dias, editais de licitação de fontes públicas e
enche uma **caixa estilo e-mail** com as **oportunidades onde o poder público
contrata serviços tipo-LexFlow** — clipping, monitoramento de publicações
oficiais, captura de Diário de Justiça (DJE), recorte de publicações, software
jurídico e afins. Um **digest diário** resume o dia e o estado dos *projetos de
interesse*.

**NÃO é:**
- uma ferramenta forense (isso é o LexFlow);
- um radar de editais de serviços advocatícios (contratação de advogados) — essa
  família fica **fora de âmbito** no MVP;
- um produto multi-tenant/SaaS — é **ferramenta interna de operador único**.

**Alvo do matching:** licitações cujo **objeto** é um serviço do tipo que o
LexFlow vende. O produto existe para **encontrar oportunidades de venda**.

## 2. Decisões travadas no brainstorming

| Decisão | Escolha |
|---|---|
| Relação com o LexFlow | **Standalone** novo; copia o *padrão* arquitetural, não acopla código |
| Stack | Python 3 + **FastAPI** + **PostgreSQL** + scheduler; frontend **Next.js** |
| Utilizadores | **Operador único** — sem multi-tenant, sem RLS, auth simples |
| Canais do digest | **E-mail + Telegram + página no portal** (os três) |
| Portal | **Next.js completo** (caixa rica: filtros, busca, ações) |
| Motor de relevância (MVP) | **Keyword + regras** (determinístico), com porta pronta p/ LLM |
| Fontes na Fase 1 | **PNCP + Compras.gov.br** (as duas desde o MVP) |
| Arquitetura | **Hexagonal** desde o início — portas devolvem tipo de domínio |

## 3. Fontes públicas (engenharia reversa)

### 3.1 PNCP — fonte primária obrigatória
Base: `https://pncp.gov.br/api/consulta` (consulta pública, **sem auth**).

- **Consulta por data de publicação:**
  `GET /v1/contratacoes/publicacao?dataInicial=AAAAMMDD&dataFinal=AAAAMMDD&codigoModalidadeContratacao={int}&pagina={int}&tamanhoPagina={<=500}`
  Opcionais: `uf`, `codigoMunicipioIbge`, `cnpj`, `codigoModoDisputa`.
  Resposta paginada: `totalRegistros`, `totalPaginas`, `numeroPagina`.
- **Propostas em aberto:** `GET /v1/contratacoes/proposta?dataFinal&codigoModalidadeContratacao&pagina`.
- **Download de documentos:**
  `GET /v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos` -> lista
  Edital / Termo de Referência / ETP / Projeto Básico com **URL de download**.
- **Chave natural do edital:** `cnpj_orgao + ano + sequencial`.
- Toda contratação da Lei 14.133 passa aqui -> é a espinha da captura.
- ⚠️ A consulta exige **iterar por `codigoModalidadeContratacao`** (pregão,
  concorrência, dispensa, etc.) — não há "todas as modalidades" num pedido.

### 3.2 Compras.gov.br — fonte secundária (Fase 1)
Base: `https://dadosabertos.compras.gov.br` (REST/JSON, Swagger em
`/swagger-ui/index.html`). Módulos de licitações/contratações/itens, filtros por
data e por **CATMAT/CATSER**; âmbito sobretudo **federal (SIASG)**. Complementa o
PNCP (sobreposição parcial -> dedup obrigatório entre fontes).

### 3.3 Modus operandi dos benchmarks (a copiar)
ConLicitação, Effecti, Radar de Licitações, licitagov.org: o utilizador regista
**palavras-chave** (e, nos players, CNAE); um **radar** varre PNCP/Compras.gov/
Diários **24/7**; **deduplica**; classifica por perfil; entrega **boletim diário
segmentado** por e-mail/WhatsApp/Slack; busca por termo **no objeto e no texto do
edital**; oferece **gestão dos documentos**. MyLicitacoes reproduz este ciclo em
escala de operador único.

## 4. Arquitetura (hexagonal)

```
app/
  domain/            # puro, sem I/O, sem framework
    edital.py            Edital, ScoreRelevancia, StatusCaixa
    projeto.py           ProjetoInteresse
    relevancia.py        classificar_relevancia(objeto, texto, lexico) -> ScoreRelevancia
    dedup.py             chave_natural(), deduplicar()
    digest.py            montar_digest(dia, editais, projetos) -> Digest
  ports/
    fonte_editais.py     FonteEditais.buscar(janela) -> list[Edital]
    armazenamento.py     ArmazenamentoEditalPdf.guardar(arquivo) -> RefArquivo
    canal_digest.py      CanalDigest.enviar(digest) -> None
    classificador.py     ClassificadorRelevancia.classificar(edital) -> ScoreRelevancia
  adapters/
    fontes/pncp.py
    fontes/compras_gov.py
    armazenamento/disco.py
    notificacao/email.py
    notificacao/telegram.py
    notificacao/portal.py
    classificador/keyword.py      # MVP
    # classificador/llm.py        # Fase 2 (troca por configuracao)
  db/                  # SQLAlchemy + Postgres
  api/                 # FastAPI: endpoints que servem a caixa Next.js
  scheduler/           # job diario incremental
frontend/              # Next.js — caixa estilo e-mail
```

⛔ **A seta aponta para dentro.** `domain/` não importa SQLAlchemy, FastAPI,
httpx nem adapters. As **portas devolvem tipos de domínio** (`Edital`,
`ScoreRelevancia`), nunca JSON cru nem `dict` da API. A escolha de fonte,
armazenamento e classificador faz-se **por configuração, na construção** — nunca
por `if` dentro de quem chama.

## 5. Modelo de dados (PostgreSQL)

- **edital**
  `id` (PK) · `fonte` (`pncp`|`compras_gov`) · `chave_natural` (única por fonte) ·
  `hash_conteudo` · `objeto` · `orgao_nome` · `orgao_cnpj` · `uf` · `municipio` ·
  `modalidade` · `valor_estimado` · `data_publicacao` · `data_abertura` ·
  `data_fim_propostas` · `score_relevancia` · `motivo_relevancia` (termos que
  casaram) · `status` (`novo`|`lido`|`arquivado`|`oportunidade`) · `url_origem` ·
  `capturado_em`.
  *Índice único:* `(fonte, chave_natural)`. *Índice:* `(data_publicacao)`,
  `(score_relevancia)`, `(status)`.
- **arquivo_edital**
  `id` · `edital_id` (FK, **ON DELETE CASCADE**) · `tipo`
  (`edital`|`tr`|`etp`|`pb`) · `caminho_local` · `hash` · `baixado_em`.
- **projeto_interesse**
  `id` · `nome` · `palavras_chave` (lista) · `filtros` (JSONB: uf, modalidade,
  faixa de valor, órgão) · `ativo` · `criado_em`.
- **execucao_captura**
  `id` · `fonte` · `janela_inicio` · `janela_fim` · `total_lidos` · `total_novos` ·
  `total_relevantes` · `status` (`sucesso`|`falha`|`parcial`) · `erro` ·
  `iniciado_em` · `terminado_em`. Guarda `ultima_captura_em` por fonte (marca da
  janela incremental).
- **digest_log**
  `id` · `data_ref` · `canais` · `enviado_em` · `resumo` (JSONB).

> Toda FK de dados do utilizador declara `ON DELETE` explícito (lição LexFlow:
> FK sem `ON DELETE` torna o registo indelével).

## 6. Fluxo diário (o agente autónomo)

1. **Scheduler** dispara a execução no horário configurado (ex.: 06:00).
2. Janela **incremental**: de `ultima_captura_em` da fonte até agora (após a 1.ª
   sincronização; a 1.ª varre uma janela inicial configurável, ex.: 7 dias).
3. Para cada `FonteEditais` (PNCP, Compras.gov), para cada modalidade relevante:
   `buscar(janela)` -> `list[Edital]` normalizado (paginação até esgotar).
4. **Dedup** por `(fonte, chave_natural)` + `hash_conteudo`; dedup **entre** fontes
   por heurística (mesmo órgão + objeto + datas).
5. `ClassificadorRelevancia.classificar(edital)` -> `ScoreRelevancia` + motivo.
6. Persiste novos/atualizados; enfileira **download do PDF** dos relevantes
   (score >= piso) -> `ArmazenamentoEditalPdf.guardar`.
7. `montar_digest(hoje, relevantes, projetos)` -> envia por **e-mail + Telegram** e
   grava na **página** `/digest/hoje`.
8. Regista `execucao_captura` e `digest_log`.

## 7. Motor de relevância (MVP determinístico)

- **Léxico curado** com termos + sinónimos + **negativos**, versionado no repo:
  positivos — "clipping", "monitoramento de publicações", "recorte de
  publicações", "diário oficial/justiça", "DJE", "acompanhamento processual",
  "software/sistema jurídico", "gestão de publicações"…; negativos que abatem
  score — termos que provocam falso positivo (a apurar com dados reais).
- **Score por cobertura** da massa de termos presente em `objeto + texto`, com
  **piso configurável** para entrar como "relevante". Guarda `motivo_relevancia`
  (quais termos casaram) — decisão **explicável**.
- `ClassificadorRelevancia` é **porta**; o `keyword.py` é o adaptador do MVP. Na
  Fase 2, `llm.py` faz *coarse->LLM* (BYOK, padrão LexFlow) e liga-se por
  configuração, **sem tocar** no fluxo diário.

## 8. Caixa + Digest (portal Next.js)

- **Caixa**: lista estilo e-mail (não-lidos em destaque, badge de score e de
  prazo), detalhe do edital com metadados + link/preview do PDF, ações
  **ler / arquivar / marcar oportunidade**, filtros (UF, modalidade, fonte,
  projeto de interesse), busca full-text no objeto.
- **Digest**: `/digest/hoje` é a **fonte canónica**; e-mail (HTML claro, padrão
  LexFlow) e Telegram são **espelhos**. Conteúdo: (a) *status do dia* — nº de
  novos, relevantes, downloads, falhas de fonte; (b) *status por projeto de
  interesse* — "Projeto X: N novos, M com prazo a fechar".
- **Projeto de interesse** = busca salva e nomeada (palavras-chave + filtros) que
  o agente rastreia e que ganha **linha própria** no digest. MVP: estrutura de
  dados + presença no digest; UI de gestão rica -> Fase 2.

## 9. Tratamento de erros (lições LexFlow embutidas)

- **Isolamento por fonte:** uma fonte lenta/caída **não zera** as outras (cada
  fonte é uma execução própria; falha marca `parcial`, não aborta o dia).
- **Captura incremental idempotente:** re-correr a mesma janela não duplica.
- **Download** com retry/backoff; PDF que falha não bloqueia o edital na caixa.
- **Piso declarado:** a execução regista `total_lidos`; varredura que leu **zero**
  numa janela onde havia expectativa de dados é **falha visível**, não verde.
- **Dedup à prova de silêncio:** dedup por hash de conteúdo, nunca só por chave —
  para não silenciar um edital retificado.
- **TLS:** algumas fontes públicas mandam cadeia incompleta (lição TCDF) — o
  cliente HTTP usa contexto com bundle (`certifi` + fallback) desde o início.

## 10. Estratégia de testes (TDD por mutação)

- **Unit** (sem I/O): `classificar_relevancia` (léxico e piso), `deduplicar`,
  `montar_digest`, e os **parsers** de PNCP e Compras.gov a partir de **fixtures
  JSON reais** (capturadas uma vez das APIs).
- **Integração** (Postgres real): captura -> persistência -> estados da caixa.
- **E2E** (stack em contentores): **fake ao nível do fio** — um servidor HTTP que
  imita PNCP e Compras.gov (contrato: paginação, cabeçalhos, corpo) — **nunca**
  monkeypatch do nosso código. Valida captura -> caixa -> digest ponta a ponta.
- **UI**: Playwright (chromium headless) na caixa Next.js.
- Cada guarda **declara piso** (imprime quantos cenários/registos correu; falha
  com zero).

## 11. Segurança e configuração

- Segredos (SMTP, token Telegram, futura chave BYOK) **só em `.env`**, nunca no
  código nem versionados. `NEXT_PUBLIC_*` só para o que é realmente público.
- Sem PII de terceiros no MVP (editais são dados públicos); ainda assim, download
  de PDF vai para pasta local controlada, fora do controlo de versões.
- Rate-limit/educação com as APIs públicas (backoff, `tamanhoPagina` alto para
  reduzir nº de chamadas).

## 12. Faseamento (resumo — detalhe no PRD)

- **Fase 1 — Radar PNCP + Compras.gov + Caixa + Digest.** Captura diária das duas
  fontes, matching keyword, caixa Next.js (lista/detalhe/ler/arquivar/oportunidade),
  download do edital, digest e-mail+Telegram+página. **Produto mínimo utilizável.**
- **Fase 2 — Classificador LLM + Projetos de Interesse (UI) + fontes extra.**
  Coarse->LLM por configuração; UI de gestão de projetos de interesse; segmentação
  do digest por projeto.
- **Fase 3 — Diários Oficiais/DJE + Kanban de oportunidades + enriquecimento**
  (prazo, valor, contacto do órgão), e possível exportação/integração com o LexFlow.

## 13. Fora de âmbito (MVP)

- Multi-tenant / RLS / contas de vários escritórios.
- Editais de serviços advocatícios (contratação de advogados).
- Submissão de propostas / robô de disputa (os players fazem; nós **não**).
- Armazenamento em nuvem (S3/Magalu) — a porta existe, o adaptador de disco chega.
