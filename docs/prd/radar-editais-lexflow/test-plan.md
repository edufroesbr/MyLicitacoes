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
- [ ] captura -> persistência: novos inseridos, existentes não duplicados
- [ ] índice único `(fonte, chave_natural)` impede duplicado
- [ ] `execucao_captura` grava contadores e status (`sucesso`/`parcial`/`falha`)
- [ ] FK `arquivo_edital -> edital` com `ON DELETE CASCADE` remove arquivos ao apagar edital

### Isolamento de falhas
- [ ] Fonte A cai, fonte B continua: dia marcado `parcial`, editais de B persistidos
- [ ] Janela incremental re-corrida não duplica (idempotência)
- [ ] Varredura que leu zero numa janela com dados esperados = falha visível (piso)

### E2E (fake ao nível do fio, contentores)
- [ ] Fake HTTP imita PNCP (`/v1/contratacoes/publicacao` paginado + `/arquivos`)
- [ ] Fake HTTP imita Compras.gov (consulta por data)
- [ ] Fluxo: captura -> matching -> caixa populada -> PDF baixado -> digest gerado
- [ ] Digest chega ao coletor de e-mail falso e ao stub de Telegram; página `/digest/hoje` renderiza
- [ ] Piso declarado: passo imprime nº de cenários/editais; falha com zero

### UI (Playwright)
- [ ] Caixa lista editais; não-lidos em destaque; badge de score
- [ ] Detalhe abre com link do PDF
- [ ] Ações ler / arquivar / marcar oportunidade refletem no backend
- [ ] Filtros (UF/modalidade/fonte/projeto) e busca no objeto funcionam

### Revisões (portas 6-8)
- [ ] `/code-review xhigh`: __ achados (colar resumo)
- [ ] `/ponytail-review`: __ achados (colar resumo)

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
