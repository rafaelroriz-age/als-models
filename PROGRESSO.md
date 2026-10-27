# Progresso — ALS OilModel

Dashboard em tempo real do status do backlog. Atualizado por `scripts/run_backlog.py status` e consolidado pelo Fechamento de Lote (ver [BACKLOG.md](BACKLOG.md)).

Última atualização: **27/10/2026 — não iniciado**

---

## Visão geral

| Fase | Status | Tarefas | Próximos passos |
|------|--------|---------|---|
| **A. Acesso e dados reais** | 🔴 não iniciado | T01–T05 | Disparar T01 (diagnóstico de porta 1433) |
| **B. Código offline** | 🔴 não iniciado | T06–T13 | Rodar em paralelo com A |
| **C. Modelagem com dados** | 🔴 bloqueado por A | T14–T19 | Espera A terminar |
| **D. Entrega** | 🔴 bloqueado por C | T20–T22 | Espera C terminar |
| **E. Decisões e comunicação** | 🟡 humano | T23–T24 | T23 paralelo com tudo; T24 após T23 |

---

## Bloco A — Acesso e Fase 0 (dados reais)

| Tarefa | Papel | Status | Saída | Atualizado |
|--------|-------|--------|-------|-----------|
| T01 | 🏗️ Engenheiro SW | 🔴 `todo` | Diagnóstico 1433/443 | — |
| T02 | 📊 Analista | 🔴 `todo` (depende T01) | Perfil de qualidade | — |
| T03 | 📊 Analista | 🔴 `todo` (depende T02) | Taxa de casamento de chaves | — |
| T04 | 📊 Analista | 🔴 `todo` (depende T02, T03) | Matriz de cobertura | — |
| T05 | 🔬 Especialista | 🔴 `todo` (depende T02) | Origem do potencial + equipamento ativo | — |

**Saída esperada do bloco:** caminho para rodar o perfil (se porta 1433 estiver bloqueada) e dados das matrizes/chaves armazenados em `data/perfil/`.

---

## Bloco B — Código offline

| Tarefa | Papel | Status | Saída | Atualizado |
|--------|-------|--------|-------|-----------|
| T06 | 🏗️ Engenheiro SW | 🔴 `todo` | Gates G0/G1 com testes | — |
| T07 | 🔬 Especialista | 🔴 `todo` | Features de série temporal | — |
| T08 | 🔬 Especialista | 🔴 `todo` | Alertas de queda >20% e churn | — |
| T09 | 🤖 Cientista | 🔴 `todo` | Classificação de clientes | — |
| T10 | 🤖 Cientista | 🔴 `todo` | Modelos estatísticos (ETS, Theta, Croston) | — |
| T11 | 🤖 Cientista | 🔴 `todo` (depende T07) | Modelo ML global com quantis | — |
| T12 | 🏗️ Engenheiro SW | 🔴 `todo` | Snapshot e reconstrução retroativa | — |
| T13 | 🤖 Cientista | 🔴 `todo` | Reconciliação hierárquica | — |

**Saída esperada do bloco:** base de código em `src/` com gates, features, modelos e testes verdes; tudo pronto para rodar com dados reais em C.

---

## Bloco C — Modelagem com dados reais

| Tarefa | Papel | Status | Saída | Atualizado |
|--------|-------|--------|-------|-----------|
| T14 | 🏗️ Engenheiro SW | 🔴 `todo` (depende T03, T07) | Tabela-base por entidade e mês | — |
| T15 | 🤖 Cientista | 🔴 `todo` (depende T10, T11, T14) | Backtest KPI 1 (WAPE, viés, cobertura) | — |
| T16 | 🤖 Cientista | 🔴 `todo` (depende T05, T14) | Potencial e % Achieved por cliente | — |
| T17 | 🤖 Cientista | 🔴 `todo` (depende T14) | Correlação consumo→venda, receita decomposta | — |
| T18 | 🔬 Especialista | 🔴 `todo` (depende T17) | Cross-check Zoho (oportunidades >80%) | — |
| T19 | 🤖 Cientista | 🔴 `todo` (depende T15, T17) | Documento de decisão de modelos | — |

**Saída esperada do bloco:** tabelas de forecast e MLflow com os modelos candidatos; documento recomendando qual modelo por KPI.

---

## Bloco D — Entrega

| Tarefa | Papel | Status | Saída | Atualizado |
|--------|-------|--------|-------|-----------|
| T20 | 🧠 Engenheiro IA | 🔴 `todo` (depende T15) | Dashboard HTML estático + SQL | — |
| T21 | 👔 Gestor | 🔴 `todo` (depende T20) | Comparativo H1 × H2 × H3 (esforço, custo, manutenção) | — |
| T22 | 🏗️ Engenheiro SW | 🔴 `todo` (depende T15) | FinOps: custo em CU por modelo | — |

**Saída esperada do bloco:** protótipos de entrega (HTML + SQL é o H1) e análise de custo.

---

## Bloco E — Decisões e comunicação

| Tarefa | Papel | Status | Saída | Atualizado |
|--------|-------|--------|-------|-----------|
| T23 | 👔 Gestor | 🔴 `todo` | Pauta de decisões (meta MAPE, cadência, Zoho hierarquia, CU, fórmula março, status manual, destino publicação) | — |
| T24 | 📋 Organizador | 🔴 `todo` (depende T23) | Apresentação executiva reescrita | — |

**Saída esperada do bloco:** pauta e apresentação atualizadas para validação com o cliente.

---

## Lotes rodados

### Lote 1 — Offline + Diagnóstico (próximo)
**Tarefas:** T01 (diagnóstico), T06–T13 (código), T23 (pauta humana)  
**Quando:** comando `python scripts/run_backlog.py run --ambiente offline`  
**Status:** ⏳ **não iniciado**

#### Detalhes
- Dispara 9 agentes em paralelo em worktree isolado.
- T01 identifica o caminho para acessar o SQL endpoint (porta 1433, VPN ou Fabric).
- T06–T13 criam a base de código (gates, features, modelos, testes).
- T23 levanta a pauta de decisões do negócio (humano, não automático, mas copiável).
- Fechamento de lote consolida docs_fabric/06 (fases), 12 (etapas) e 13 (decisões).

---

### Lote 2 — Acesso e dados (depois de Lote 1 + T01 ✅)
**Tarefas:** T02–T05  
**Quando:** `python scripts/run_backlog.py run --ambiente fabric` (depois que T01 disser que a porta 1433 está ok)  
**Status:** 🔴 **bloqueado por T01**

#### Detalhes
- Depende do resultado de T01 (diagnóstico).
- Se 1433 estiver ok: rode aqui.
- Se bloqueado: T02–T05 viram tarefa de "pedir ao TI" ou "rodar dentro do Fabric manualmente".

---

### Lote 3 — Modelagem com dados (depois de Lote 2 + Lote 1)
**Tarefas:** T14–T19  
**Quando:** após T03 ✅ (chaves), T07 ✅ (features), T10–T11 ✅ (modelos) e T05 ✅ (potencial)  
**Status:** 🔴 **bloqueado por A + B**

---

### Lote 4 — Entrega (depois de Lote 3)
**Tarefas:** T20–T22  
**Quando:** após T15 ✅ (backtest KPI 1) e T17 ✅ (KPI 2)  
**Status:** 🔴 **bloqueado por C**

---

### Lote 5 — Apresentação (depois de Lote E.T23)
**Tarefas:** T24  
**Quando:** após T23 ✅ (pauta)  
**Status:** 🔴 **bloqueado por T23**

---

## Como acompanhar

| Ação | Comando | Saída |
|------|---------|-------|
| Ver status geral | `python scripts/run_backlog.py status` | Tarefas concluídas, em progresso, bloqueadas |
| Disparar o próximo lote | `python scripts/run_backlog.py run --ambiente offline` | Agentes em background, PIDs e logs |
| Simular (sem disparar) | `python scripts/run_backlog.py run --ambiente offline --dry` | O que seria disparado |
| Ver status do backlog | `python scripts/backlog.py list` | Todas as tarefas com status |
| Copiar prompt de uma tarefa | `python scripts/backlog.py show T07` | Pronto para colar em um agente |
| Atualizar status manualmente | `python scripts/backlog.py set T01 done` | Status no BACKLOG.md |
| Acompanhar logs de agentes | Ver `logs/lote_*.log` | Stdout/stderr de cada agente |

---

## Checklist para disparar

Antes de rodar `python scripts/run_backlog.py run`:

- [ ] Leia [BACKLOG.md](BACKLOG.md) (visão geral dos 24 prompts)
- [ ] Leia [AGENTS.md](AGENTS.md) (papéis e regra de documentação)
- [ ] Confirme que o `pyproject.toml` está atualizado com todas as dependências necessárias
- [ ] Confirme que `src/`, `tests/`, `notebooks/` e `scripts/` estão em `.gitignore` (ou apenas `data/` está)
- [ ] Está pronto para reunião com o time caso T23 termine primeiro (pauta de decisões)

---

## FAQ

**P: E se um agente falhar?**  
R: O log fica em `.claude/logs/`. Copie manualmente o prompt do `python scripts/backlog.py show Txx`, ajuste se necessário, e rode de novo. Depois `python scripts/backlog.py set Txx doing` ou `done` conforme resultado.

**P: Posso rodar tarefas de ambientes diferentes em paralelo?**  
R: Sim! O script seleciona só as que estão liberadas pelas dependências. `--ambiente offline` filtra as offline (seguras em background); `--ambiente fabric` filtra as que precisam do SQL endpoint. Saia de um `--ambiente` e entre em outro conforme o resultado de T01.

**P: Como faço se T01 disser que a porta 1433 está bloqueada?**  
R: Siga o plano B que T01 vai sugerir (VPN, pedido ao TI, ou rodar dentro do Fabric). O BACKLOG.md não precisa de mudanças; só o resultado de T01 vai pra docs_fabric/14 §4.

**P: E a consolidação de 06/12/13?**  
R: Cole o prompt "Fechamento de lote" do BACKLOG.md depois de cada lote. Usa `git diff` para ver o que cada agente mexeu, atualiza as seções, move hipóteses/descobertas para docs_fabric/13 §3, marca `[x]` em docs_fabric/06, atualiza status em docs_fabric/12.

**P: Posso editar tarefas do BACKLOG.md?**  
R: Sim. Se a tarefa virou inútil: `python scripts/backlog.py set Txx blocked` (não é mais `todo`). Se precisa de ajuste: edite o `.md` e rode de novo (o script lê tudo do zero).

