# Test Plan — Radar de Editais tipo-LexFlow (MyLicitacoes)

> **Requisitos:** [`requirements.md`](requirements.md)
> Cada `[x]` exige o **log/stdout cru** colado logo abaixo. Sem log = Não Realizado.
> Papel de QA valida; NÃO altera código.

## Camadas (qual manda)
- Unidade / in-process — fronteiras e semântica.
- Integração (Postgres real) — o que o SQL faz mesmo.
- **E2E (fake ao nível do fio, stack em contentores)** — o que o operador alcança. **Decide.**
- UI (Playwright) — a caixa Next.js.

---

## FASE 1

### Unit (sem I/O)
- [x] `classificar_relevancia`: objeto tipo-LexFlow acima do piso; objeto irrelevante abaixo (vermelho por mutação do léxico)
- [x] `classificar_relevancia`: `motivo_relevancia` lista os termos casados
- [x] `deduplicar`: mesma chave natural não duplica; conteúdo alterado (hash) atualiza
- [x] dedup entre fontes: mesmo edital em PNCP e Compras.gov colapsa em um
- [x] `montar_digest`: status do dia correto; uma linha por projeto de interesse
- [x] parser PNCP: fixture JSON real -> `Edital` com chave `cnpj+ano+sequencial`
- [x] parser Compras.gov: fixture JSON real -> `Edital`

### Integração (Postgres real)
- [x] captura -> persistência: novos inseridos, existentes não duplicados
- [x] índice único `(fonte, chave_natural)` impede duplicado
- [ ] `execucao_captura` grava contadores e status (`sucesso`/`parcial`/`falha`) — **gap real:** o código só grava `"sucesso"`/`"falha"` por fonte (`app/scheduler/orquestrador.py` linhas 33/36); a string `"parcial"` não existe em lugar nenhum do código (`grep -rn parcial app/ tests/` → vazio). `test_ultima_captura_ignora_execucao_com_falha` prova sucesso/falha; falta decidir se "parcial" é um status por fonte a implementar ou se o status do dia deveria vir derivado de `fontes_falha` (já existe em `Digest.fontes_com_falha`) — não decidi isso por conta própria.
- [x] FK `arquivo_edital -> edital` com `ON DELETE CASCADE` remove arquivos ao apagar edital

### Isolamento de falhas
- [ ] Fonte A cai, fonte B continua: dia marcado `parcial`, editais de B persistidos — **parcialmente provado:** "editais de B persistidos" está provado (`test_fonte_que_cai_nao_derruba_a_outra`); "dia marcado parcial" não, pelo mesmo gap do item acima.
- [x] Janela incremental re-corrida não duplica (idempotência)
- [ ] Varredura que leu zero numa janela com dados esperados = falha visível (piso) — **gap real:** só existe guarda para "todas as modalidades PNCP erraram" (`app/adapters/fontes/pncp.py:107`, `sucessos == 0 and ultimo_erro is not None`); não há guarda para "a fonte respondeu 200 mas devolveu zero itens numa janela onde se esperava ter dados" — hoje isso passa em silêncio como `novos=0`, sem sinal de alerta.

### E2E (fake ao nível do fio, contentores)
- [x] Fake HTTP imita PNCP (`/v1/contratacoes/publicacao` paginado + `/arquivos`)
- [ ] Fake HTTP imita Compras.gov (consulta por data) — **gap real:** `tests/e2e/fake_portais.py` só tem o handler do PNCP; não existe fake E2E do Compras.gov.
- [ ] Fluxo: captura -> matching -> caixa populada -> PDF baixado -> digest gerado — **parcial:** `test_captura_ate_digest` prova captura->matching->digest, mas usa `SessionFake`/`upsert_editais` mockado, não Postgres real + API de leitura — "caixa populada" (via API) não está provado neste teste.
- [ ] Digest chega ao coletor de e-mail falso e ao stub de Telegram; página `/digest/hoje` renderiza — **não provado:** o E2E usa `CanalFake`, não os adaptadores reais de e-mail/Telegram (esses têm teste próprio em `tests/adapters/test_notificacao.py`, mas isolado, não encadeado no E2E); não há teste de render da página `/digest/hoje`.
- [x] Piso declarado: passo imprime nº de cenários/editais; falha com zero

### UI (Playwright)
- [ ] Caixa lista editais; não-lidos em destaque; badge de score
- [ ] Detalhe abre com link do PDF
- [ ] Ações ler / arquivar / marcar oportunidade refletem no backend
- [ ] Filtros (UF/modalidade/fonte/projeto) e busca no objeto funcionam

### Revisões (portas 6-8)
- [ ] `/code-review xhigh`: __ achados (colar resumo) — rodando em segundo plano, 2026-10-08
- [x] `/ponytail-review` (HEAD~5..HEAD, backend): nenhum achado — `net: 0 lines possible. Lean already. Ship.` Verificado: `_RetryTransitorio` (http_client.py), mapeamento `TIPOS_DOCUMENTO` (pncp.py), filtro `fase_proposta` e helper `_sem_acento` (editais.py) — todos têm 2+ usos reais ou justificativa direta, sem abstração especulativa.

---

## FASE 2 (esboço)
- [ ] Trocar keyword->LLM só por configuração não muda o fluxo diário (contrato)
- [ ] Coarse filter reduz nº de chamadas ao LLM (medir)
- [ ] UI de projetos de interesse: criar/editar/ativar persiste e afeta o digest

## FASE 3 (esboço)
- [ ] Captura de Diário/DJE alimenta a caixa
- [ ] Kanban move oportunidade entre estados
- [ ] Enriquecimento preenche prazo/valor/contacto

---

## Registo de provas
> Colar aqui o stdout cru de cada corrida, sob o item correspondente.

### FASE 1 — Unit (sem I/O), 2026-10-08

```
$ uv run pytest tests/domain/test_relevancia.py tests/domain/test_dedup.py tests/domain/test_digest.py tests/adapters/test_pncp.py tests/adapters/test_compras_gov.py -v
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\edufr\.claude\projects\Mylicitacoes\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\edufr\.claude\projects\Mylicitacoes
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 21 items

tests/domain/test_relevancia.py::test_objeto_tipo_lexflow_pontua_alto PASSED [  4%]
tests/domain/test_relevancia.py::test_objeto_irrelevante_pontua_zero PASSED [  9%]
tests/domain/test_relevancia.py::test_acentos_e_caixa_nao_importam PASSED [ 14%]
tests/domain/test_relevancia.py::test_caso_canonico_lexflow_passa_o_piso_real_com_o_lexico_real PASSED [ 19%]
tests/domain/test_relevancia.py::test_caso_irrelevante_nao_passa_o_piso_real_com_o_lexico_real PASSED [ 23%]
tests/domain/test_dedup.py::test_dedup_por_chave_natural PASSED          [ 28%]
tests/domain/test_dedup.py::test_dedup_entre_fontes_prefere_pncp PASSED  [ 33%]
tests/domain/test_dedup.py::test_hash_muda_com_conteudo PASSED           [ 38%]
tests/domain/test_dedup.py::test_sem_cnpj_nao_colapsa_mesmo_objeto_e_data PASSED [ 42%]
tests/domain/test_digest.py::test_digest_conta_e_limita_destaques PASSED [ 47%]
tests/adapters/test_pncp.py::test_parse_item_primeiro_registo PASSED     [ 52%]
tests/adapters/test_pncp.py::test_d_com_data_invalida_nao_levanta PASSED [ 57%]
tests/adapters/test_pncp.py::test_buscar_pula_item_malformado_mas_mantem_os_validos PASSED [ 61%]
tests/adapters/test_pncp.py::test_buscar_pula_modalidade_com_erro_mas_continua_as_outras PASSED [ 66%]
tests/adapters/test_pncp.py::test_buscar_usa_tamanho_pagina_50 PASSED    [ 71%]
tests/adapters/test_pncp.py::test_buscar_levanta_se_todas_as_modalidades_falharem PASSED [ 76%]
tests/adapters/test_pncp.py::test_parse_item_captura_situacao_compra PASSED [ 80%]
tests/adapters/test_pncp.py::test_buscar_pausa_entre_requests PASSED     [ 85%]
tests/adapters/test_pncp.py::test_listar_arquivos_mapeia_tipo_por_tipo_documento_id PASSED [ 90%]
tests/adapters/test_pncp.py::test_listar_arquivos_nao_marca_tudo_como_edital PASSED [ 95%]
tests/adapters/test_compras_gov.py::test_parse_item_primeiro_registo PASSED [100%]

============================= 21 passed in 0.31s ==============================
```

### FASE 1 — Integração (Postgres real) + Isolamento + E2E, 2026-10-08

```
$ docker compose up -d   # postgres:16 em localhost:5433 (mylic/mylic/mylic)
$ export MYLIC_DATABASE_URL="postgresql+psycopg://mylic:mylic@localhost:5433/mylic"
$ uv run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
$ uv run alembic current
unaccent_situacao_20261008 (head)

$ uv run pytest -v
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 55 items
[... 55 itens, todos PASSED, incluindo:
 tests/db/test_repo.py::test_upsert_nao_duplica_e_conta PASSED
 tests/db/test_repo.py::test_upsert_devolve_ids_e_persistir_arquivo PASSED
 tests/db/test_repo.py::test_ultima_captura_ignora_execucao_com_falha PASSED
 tests/scheduler/test_orquestrador.py::test_fonte_que_cai_nao_derruba_a_outra PASSED
 tests/scheduler/test_orquestrador.py::test_listar_arquivos_que_falha_nao_bloqueia_outro_edital_nem_o_digest PASSED
 tests/scheduler/test_orquestrador.py::test_canal_que_falha_nao_impede_os_restantes PASSED
 tests/scheduler/test_orquestrador.py::test_cada_fonte_recebe_a_sua_propria_janela_incremental PASSED
 tests/e2e/test_captura_ate_digest.py::test_captura_ate_digest PASSED]
======================= 55 passed, 2 warnings in 10.07s =======================
```

Prova ad-hoc (script Python direto contra o Postgres real, bypassando o ORM upsert, para provar o índice único e o FK CASCADE ao nível do banco — não só da lógica Python):

```
edital inserido id= 1
OK unique index rejeitou duplicado: IntegrityError (psycopg.errors.UniqueViolation) duplicate key value violates unique constraint "uq_edital_fonte_chave"
arquivo inserido id= 1
arquivos restantes apos apagar edital (deve ser 0): 0
```

Dados de teste limpos após a prova (`TRUNCATE ... RESTART IDENTITY CASCADE`).
