# Progresso — ALS OilModel

> Gerado por `python scripts/run_backlog.py status` a partir do [BACKLOG.md](BACKLOG.md). Não edite à mão.

Atualizado em 27/10/2026 13:46 · **12/25 concluídas** · 3 em andamento · 10 a fazer · 0 bloqueadas

## Próximo lote (pode rodar em paralelo)

- nenhum liberado

## Sessões em background agora

- backlog-T11: idle
- backlog-T03: busy
- backlog-T05: busy

## Bloco A — Acesso e Fase 0 (dados reais) (3/6)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| ✅ | **T01** Diagnosticar a conectividade com o SQL endpoint | @engenheiro-software | offline | baixa | — |
| ✅ | **T02** Rodar o perfil de qualidade das tabelas-chave | @analista-dados | fabric | media | T01 |
| 🔄 | **T03** Validar as chaves entre fontes | @analista-dados | fabric | media | T02 |
| ⬜ | **T04** Preencher a matriz de cobertura dos insumos | @analista-dados | fabric | media | T02, T03 |
| 🔄 | **T05** Descobrir a origem do Annual Sample Potential e o status ativo do equipamento | @especialista-dados | fabric | alta | T02 |
| ✅ | **T25** Executor de notebooks no Fabric via API (sem depender da porta 1433) | @engenheiro-software | fabric | alta | — |

## Bloco B — Código que não depende de dados reais (7/8)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| ✅ | **T06** Testes e contrato de dados dos gates G0/G1 | @engenheiro-software | offline | media | — |
| ✅ | **T07** Features de série temporal por entidade e mês | @especialista-dados | offline | media | — |
| ✅ | **T08** Alertas de queda >20% e compartimento churn | @especialista-dados | offline | baixa | — |
| ✅ | **T09** Classificação de clientes (Fase 1b) sobre o Customer Status | @cientista-dados | offline | media | — |
| ✅ | **T10** Modelos estatísticos plugáveis no harness | @cientista-dados | offline | media | — |
| 🔄 | **T11** Modelo ML global com quantis | @cientista-dados | offline | alta | T07 |
| ✅ | **T12** Snapshot mensal e reconstrução retroativa | @engenheiro-software | offline | media | — |
| ✅ | **T13** Reconciliação hierárquica Cliente → Equipamento → Compartimento | @cientista-dados | offline | alta | — |

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

## Bloco E — Decisões e comunicação (2/2)

| | Tarefa | Papel | Ambiente | Dificuldade | Depende |
|---|---|---|---|---|---|
| ✅ | **T23** Pauta de decisões para o time | @gestor-projetos | humano | baixa | — |
| ✅ | **T24** Regerar a apresentação executiva com o escopo atual | @organizador | offline | baixa | T23 |
