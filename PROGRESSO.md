# Progresso — ALS OilModel

> Gerado por `python scripts/run_backlog.py status` a partir do [BACKLOG.md](BACKLOG.md). Não edite à mão.

Atualizado em 27/10/2026 13:16 · **0/25 concluídas** · 9 em andamento · 16 a fazer · 0 bloqueadas

## Próximo lote (pode rodar em paralelo)

- **T23** [humano, baixa → haiku] Pauta de decisões para o time

## Sessões em background agora

- backlog-T06: waiting (permission prompt)
- backlog-T01: idle
- backlog-T08: waiting (permission prompt)
- backlog-T09: waiting (permission prompt)
- backlog-T10: waiting (permission prompt)
- backlog-T12: waiting (permission prompt)
- backlog-T25: waiting (permission prompt)
- backlog-T01: waiting (permission prompt)

## Bloco A — Acesso e Fase 0 (dados reais) (0/6)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| 🔄 | **T01** Diagnosticar a conectividade com o SQL endpoint | @engenheiro-software | offline | baixa | — |
| ⬜ | **T02** Rodar o perfil de qualidade das tabelas-chave | @analista-dados | fabric | media | T01 |
| ⬜ | **T03** Validar as chaves entre fontes | @analista-dados | fabric | media | T02 |
| ⬜ | **T04** Preencher a matriz de cobertura dos insumos | @analista-dados | fabric | media | T02, T03 |
| ⬜ | **T05** Descobrir a origem do Annual Sample Potential e o status ativo do equipamento | @especialista-dados | fabric | alta | T02 |
| 🔄 | **T25** Executor de notebooks no Fabric via API (sem depender da porta 1433) | @engenheiro-software | fabric | alta | — |

## Bloco B — Código que não depende de dados reais (0/8)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| 🔄 | **T06** Testes e contrato de dados dos gates G0/G1 | @engenheiro-software | offline | media | — |
| 🔄 | **T07** Features de série temporal por entidade e mês | @especialista-dados | offline | media | — |
| 🔄 | **T08** Alertas de queda >20% e compartimento churn | @especialista-dados | offline | baixa | — |
| 🔄 | **T09** Classificação de clientes (Fase 1b) sobre o Customer Status | @cientista-dados | offline | media | — |
| 🔄 | **T10** Modelos estatísticos plugáveis no harness | @cientista-dados | offline | media | — |
| ⬜ | **T11** Modelo ML global com quantis | @cientista-dados | offline | alta | T07 |
| 🔄 | **T12** Snapshot mensal e reconstrução retroativa | @engenheiro-software | offline | media | — |
| 🔄 | **T13** Reconciliação hierárquica Cliente → Equipamento → Compartimento | @cientista-dados | offline | alta | — |

## Bloco C — Modelagem com dados reais (0/6)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| ⬜ | **T14** Tabela-base por entidade e mês | @engenheiro-software | fabric | alta | T03, T07 |
| ⬜ | **T15** Backtest do KPI 1 com os candidatos em dados reais | @cientista-dados | fabric | alta | T10, T11, T14 |
| ⬜ | **T16** KPI 1 Potencial: benchmark por similares e % Achieved | @cientista-dados | fabric | alta | T05, T14 |
| ⬜ | **T17** KPI 2: correlação consumo → venda e composição da receita | @cientista-dados | fabric | alta | T14 |
| ⬜ | **T18** KPI 2: cross-check com Zoho sem dupla contagem | @especialista-dados | fabric | media | T17 |
| ⬜ | **T19** Documento de decisão de modelos | @cientista-dados | offline | media | T15, T17 |

## Bloco D — Entrega (0/3)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| ⬜ | **T20** Protótipo H1: dashboard HTML + SQL | @engenheiro-ia | offline | media | T15 |
| ⬜ | **T21** Comparativo das opções de entrega | @gestor-projetos | offline | baixa | T20 |
| ⬜ | **T22** FinOps: custo em CU por experimento | @engenheiro-software | fabric | media | T15 |

## Bloco E — Decisões e comunicação (0/2)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| ⬜ | **T23** Pauta de decisões para o time | @gestor-projetos | humano | baixa | — |
| ⬜ | **T24** Regerar a apresentação executiva com o escopo atual | @organizador | offline | baixa | T23 |
