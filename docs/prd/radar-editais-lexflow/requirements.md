# PRD — Radar de Editais tipo-LexFlow (MyLicitacoes)

> **Design:** [`../../superpowers/specs/2026-09-10-radar-editais-lexflow-design.md`](../../superpowers/specs/2026-09-10-radar-editais-lexflow-design.md)
> **Plano de testes:** [`test-plan.md`](test-plan.md)
> Requisitos em checkboxes unitários. Um `[x]` só se marca com prova (ver test-plan).

## Objetivo

Agente autónomo que captura editais de licitação de fontes públicas (JSON),
enche uma **caixa estilo e-mail** com as **oportunidades tipo-LexFlow** (clipping,
monitoramento de publicações, DJE, software jurídico) e envia um **digest diário**
por e-mail + Telegram + página, incluindo o **estado dos projetos de interesse**.

## Glossário

- **Edital**: uma contratação/licitação captada de uma fonte pública.
- **Relevância**: score de o objeto do edital ser um serviço tipo-LexFlow.
- **Projeto de interesse**: busca salva e nomeada (palavras-chave + filtros) que
  o agente rastreia e que ganha linha própria no digest.
- **Digest**: boletim diário (status do dia + status por projeto de interesse).

---

## Benchmark e diferenciação

> Pesquisa de mercado (2026-10-07): ConLicitação, LicitaGov, RadarLicita,
> Edital.net, RadarPregão, BBMNET/Jornal do Licitante, Licitação Nacional,
> Monitor de Licitações, Licita Já, eLicitaRadar, Radar de Licitações
> (nocton).

**Mesa básica da categoria (todo concorrente oferece, sem exceção):**
cadastro de CNPJ/CNAE + palavras-chave como perfil; alerta automático
multicanal (e-mail, WhatsApp, Telegram, Slack); varredura diária do
PNCP/Compras.gov/Diários com boletim; busca full-text no objeto/texto do
edital; filtros por UF/modalidade/órgão/valor.

**Topo da categoria (RadarLicita, LicitaGov):** IA/LLM lê o edital e calcula
score semântico (não só keyword exata), extrai exigências/riscos, resume o
objeto; alerta de prazo de contrato vencendo (60/30/15 dias).

**Lacuna observada:** nenhum concorrente é verticalizado para o nicho
jurídico-tech (clipping, monitoramento de publicações, DJE, software
jurídico) — todos são radares horizontais genéricos; o cliente é que precisa
"ensinar" o sistema com CNAE/palavras-chave do zero.

**Conclusão para o faseamento:** "palavras-chave + alerta automático" é mesa
básica, não diferencial — por isso o matching por projeto de interesse e o
digest segmentado entram **já na Fase 1**, não na Fase 2 (ver 1.6a e 1.7).

**Diferenciais reais do MyLicitacoes:**
1. Léxico curado **vertical** tipo-LexFlow já embutido (não é o usuário que
   cadastra CNAE do zero).
2. `motivo_relevancia` explicável desde o MVP (poucos concorrentes expõem o
   "porquê" do match).
3. Múltiplos projetos de interesse nomeados na mesma operação (uma linha de
   radar por linha de serviço do LexFlow), não um único perfil por CNPJ.
4. Ferramenta interna, sem custo recorrente de SaaS terceiro, dono do dado.
5. Caixa + Kanban de oportunidades (Fase 3) cobre o funil pós-descoberta,
   algo que os genéricos não fazem.

---

## FASE 1 — Radar PNCP + Compras.gov + Caixa + Digest (MVP)

### 1.1 Fundações do projeto
- [ ] Repo `MyLicitacoes` inicializado (git) com `pyproject.toml` (uv), `.env.example`, `.gitignore`
- [ ] Estrutura hexagonal criada: `app/domain`, `app/ports`, `app/adapters`, `app/db`, `app/api`, `app/scheduler`
- [ ] PostgreSQL via `docker-compose` (postgres) + Alembic inicial
- [ ] Contrato de import (import-linter) proíbe `app.domain` importar framework/adapters

### 1.2 Domínio (puro, TDD por mutação)
- [ ] `Edital`, `ScoreRelevancia`, `StatusCaixa`, `ProjetoInteresse` definidos sem I/O
- [ ] `classificar_relevancia(objeto, texto, lexico) -> ScoreRelevancia` com score por cobertura e piso
- [ ] Léxico curado versionado (positivos + sinónimos + negativos)
- [ ] `motivo_relevancia` regista os termos que casaram (decisão explicável)
- [ ] `deduplicar()` por chave natural + `hash_conteudo`; dedup entre fontes por heurística
- [ ] `montar_digest(dia, editais, projetos) -> Digest` (status do dia + por projeto)

### 1.3 Portas e adaptadores de fonte
- [ ] Porta `FonteEditais.buscar(janela) -> list[Edital]` (devolve tipo de domínio, não JSON)
- [ ] Adaptador **PNCP**: `/v1/contratacoes/publicacao` paginado, iterando modalidades
- [ ] Adaptador PNCP: parsing -> `Edital` com chave natural `cnpj+ano+sequencial`
- [ ] Adaptador PNCP: listagem de arquivos `/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos`
- [ ] Adaptador **Compras.gov.br**: consulta por data + parsing -> `Edital`
- [ ] Cliente HTTP com contexto TLS robusto (certifi + fallback) e retry/backoff
- [ ] Cada porta nova entrega o seu contrato no import-linter no mesmo passo
- [ ] Adaptador PNCP também consome o **data lake de dados abertos** (arquivos
  em lote), não só a API de consulta paginada — há gap documentado de
  sub-contagem entre as duas (caso real: 3.171 registros via data lake vs.
  180 via API de consulta, mesmo recorte). Ver questão em aberto no fim do
  documento.

### 1.4 Armazenamento de PDF
- [ ] Porta `ArmazenamentoEditalPdf.guardar(arquivo) -> RefArquivo`
- [ ] Adaptador de **disco local** (pasta fora do controlo de versões)
- [ ] Download dos arquivos dos editais relevantes (edital/TR/ETP/PB) com hash

### 1.5 Persistência
- [ ] Modelos SQLAlchemy: `edital`, `arquivo_edital`, `projeto_interesse`, `execucao_captura`, `digest_log`
- [ ] Índice único `(fonte, chave_natural)`; FKs com `ON DELETE` explícito
- [ ] Migração Alembic (id descritivo, não sequencial) valida com `upgrade head`

### 1.6 Agente / scheduler
- [ ] Job diário incremental: janela de `ultima_captura_em` até agora (1.ª corrida = janela inicial configurável)
- [ ] Isolamento por fonte: falha de uma fonte marca `parcial`, não aborta o dia
- [ ] Execução idempotente (re-correr a janela não duplica)
- [ ] `execucao_captura` regista `total_lidos/novos/relevantes/status/erro` (piso declarado)

### 1.6a Projetos de interesse (matching, sem UI)
- [ ] CRUD mínimo de `projeto_interesse` sem UI (seed/script ou endpoint
  simples) — nome, palavras-chave, filtros, ativo
- [ ] Projeto de interesse ativo roda matching (reaproveita
  `classificar_relevancia`/léxico do projeto) contra objeto+texto de cada
  edital novo
- [ ] Seed de projeto de interesse = o próprio léxico-base tipo-LexFlow,
  validando que o mecanismo genérico serve ao caso de uso principal

### 1.7 Digest (3 canais)
- [ ] `CanalDigest.enviar(digest)` — porta
- [ ] Adaptador **e-mail** (SMTP, HTML claro padrão LexFlow)
- [ ] Adaptador **Telegram** (bot/token)
- [ ] Página `/digest/hoje` como fonte canónica; e-mail/Telegram são espelhos
- [ ] Digest inclui status do dia + linha por projeto de interesse
  (novos/relevantes/prazo a fechar) — já no MVP

### 1.8 API + Caixa (Next.js)
- [ ] Endpoints FastAPI: listar editais (filtros UF/modalidade/fonte/projeto/score), detalhe, marcar lido/arquivado/oportunidade, servir/link do PDF
- [ ] Auth simples de operador único (1 login)
- [ ] Caixa Next.js: lista estilo e-mail (não-lidos em destaque, badge de score/prazo)
- [ ] Detalhe do edital: metadados + link/preview do PDF
- [ ] Ações ler / arquivar / marcar oportunidade
- [ ] Filtros + busca full-text no objeto
- [ ] Página do digest do dia no portal

### 1.9 Revisão e verificação (portas 6-8 do ciclo)
- [ ] `/code-review xhigh` corrido antes do merge (resultado no test-plan)
- [ ] `/ponytail-review` corrido antes do merge (resultado no test-plan)
- [ ] E2E em contentores verde com piso declarado
- [ ] Nada empurrado vermelho

---

## FASE 2 — Classificador LLM + Projetos de Interesse (UI) + fontes extra
- [ ] Adaptador `classificador/llm.py` (coarse keyword -> LLM), BYOK, ligado por configuração
- [ ] Fluxo diário inalterado ao trocar de classificador (só configuração)
- [ ] UI de gestão de projetos de interesse (criar/editar/ativar/pausar) na Caixa Next.js — matching e digest já são Fase 1 (ver 1.6a/1.7)
- [ ] Fontes adicionais priorizadas por cobertura — **pesquisa 2026-10-07**:
  BEC/SP, SIGA/RJ e Compras RS não têm API comparável a PNCP/Compras.gov.br
  (só portal HTML); nenhum adaptador de scraping será construído (viola o
  princípio hexagonal "porta devolve tipo de domínio a partir de API, nunca
  HTML frágil"). Único candidato real: **MG** (SIAD/`dados.mg.gov.br`, dataset
  de dados abertos de verdade, ainda que em dump periódico). MG só entra se
  `execucao_captura` mostrar gap de cobertura real após PNCP+Compras.gov.br
  rodarem em produção — não especulativamente.

## FASE 3 — Diários/DJE + Kanban + enriquecimento
- [ ] Captura de Diários Oficiais/DJE onde o objeto é publicado
- [ ] Kanban de oportunidades (novo -> avaliando -> proposta -> ganho/perdido)
- [ ] Enriquecimento: prazo, valor, contacto do órgão
- [ ] Exportação / possível integração com o LexFlow

---

## Fora de âmbito (MVP)
- [ ] (NÃO) Multi-tenant / RLS
- [ ] (NÃO) Editais de serviços advocatícios (contratação de advogados)
- [ ] (NÃO) Submissão de propostas / robô de disputa
- [ ] (NÃO) Armazenamento em nuvem (porta existe; adaptador de disco chega)

## Questões em aberto (a resolver no plano ou com dados reais)
- [ ] Léxico inicial: termos positivos/negativos definitivos (calibrar com amostra real do PNCP)
- [ ] Modalidades PNCP a varrer (todas vs. subconjunto) e horário do job
- [ ] Heurística de dedup entre PNCP e Compras.gov (campos e tolerância)
- [ ] Piso de score para "relevante" e para acionar download
- [ ] Formato/periodicidade do consumo do data lake PNCP (arquivos em lote) e
  como reconciliar com a API de consulta paginada sem duplicar (ver 1.3)
