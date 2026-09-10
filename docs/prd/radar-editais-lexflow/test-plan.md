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
- [ ] `classificar_relevancia`: objeto tipo-LexFlow acima do piso; objeto irrelevante abaixo (vermelho por mutação do léxico)
- [ ] `classificar_relevancia`: `motivo_relevancia` lista os termos casados
- [ ] `deduplicar`: mesma chave natural não duplica; conteúdo alterado (hash) atualiza
- [ ] dedup entre fontes: mesmo edital em PNCP e Compras.gov colapsa em um
- [ ] `montar_digest`: status do dia correto; uma linha por projeto de interesse
- [ ] parser PNCP: fixture JSON real -> `Edital` com chave `cnpj+ano+sequencial`
- [ ] parser Compras.gov: fixture JSON real -> `Edital`

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
