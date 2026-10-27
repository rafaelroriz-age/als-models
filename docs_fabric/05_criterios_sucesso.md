# Critérios de Sucesso e Avaliação

## Contexto

Hoje **não há medição de assertividade** do forecast. O sucesso passa a ser medido retroativamente, com uma linha de base desde o início.

## Métodos de avaliação

1. **Snapshot mensal** — congelar o forecast previsto a cada mês e comparar com o faturamento/consumo realizado.
2. **Reconstrução retroativa** — aplicar a regra atual "como se fosse" cada mês passado sobre o histórico do Fabric e comparar com o realizado (gera linha de base imediata).
3. **Validação de dados** — great expectations / pytest nos notebooks, como parte da metodologia (não só acurácia do modelo, mas sanidade dos dados).

## Métricas

| KPI | Métrica |
|-----|---------|
| Consumo de amostras | MAPE / MAE por mês, por segmento e por cliente |
| Vendas: faturamento | MAPE / MAE por mês, por segmento e por cliente |
| Vendas: EBIT (target separado) | MAPE / MAE por mês e por segmento |
| Convergência | Acompanhar o erro ao longo do mês (a planilha atual converge perto do dia 20) |

## Formato do snapshot e da reconstrução (implementado em `src/backtest/snapshot.py`, T12)

**Snapshot** = uma linha por (corte, modelo, id, período previsto), gravado em `<raiz>/corte=YYYY-MM-DD/snapshot.csv` (`gravar_snapshot` / `ler_snapshots`; raiz em `data/` ou `Files/als_oilmodel/`, nunca sobre tabelas existentes do Fabric). Uma data de corte por arquivo; regravar a mesma data substitui só aquele arquivo.

| Coluna | Significado |
|---|---|
| `corte` | data em que o forecast foi congelado |
| `versao_modelo` | rótulo/versão do modelo (ex.: commit ou run MLflow) |
| `versao_dados` | hash de 12 caracteres da série de treino (`versao_dados()`), independente da ordem das linhas |
| `modelo`, `id` | modelo candidato e entidade prevista (cliente/equipamento/compartimento) |
| `periodo`, `horizonte` | mês previsto (1º dia) e meses entre o mês do corte e o previsto (0 = mês corrente) |
| `yhat` (+ `yhat_lo`, `yhat_hi`, `segmento` se existirem) | previsão, intervalo e segmento |

**Reconstrução retroativa** (`reconstruir`): para cada data de corte passada o modelo é reexecutado só com linhas `disponivel_em ≤ corte` (sem a coluna, o mês fica disponível no último dia dele), sem ver o futuro; produz snapshots no mesmo formato, com a linha de base imediata.

**Erro** (`erro_por`): MAPE (ignora y=0), WAPE, MAE, viés e sMAPE por qualquer combinação de `periodo`, `segmento`, `id`, opcionalmente fixando o `horizonte`. **Convergência** (`convergencia`): erro de cada mês-alvo em função de `dias_para_fim` (fim do mês-alvo − corte); cortes depois do fim do mês são descartados. Requer vários cortes dentro do mês (ex.: dias 5, 10, 20, 31) para ver a curva (a planilha atual converge perto do dia 20).

Status: validado só com dados sintéticos (`tests/test_snapshot.py`); sem números reais até a T14/T15.

## Critérios complementares

- **Convergência temporal**: o forecast semanal deve convergir para o realizado à medida que o período avança.
- **Correlação consumo→venda**: quantificar corretamente a relação entre amostras processadas e faturamento (a "projeção por amostra" da planilha).
- **Sinais de ação**: detectar queda >20% nas amostras e "compartimento churn" (a avaliação de valor comercial, além da acurácia pura).
- **Calibração de incerteza** (se intervalo for entregue): a faixa reportada deve conter o realizado na proporção declarada.

## Critério de sucesso do entregável

- Modelo **consumível pelo ambiente** (modelo semântico ou API/endpoint), não um notebook.
- Roda na capacidade F8 sem degradar o agente (FinOps respeitado).
- Transparência de metodologia/ferramentas e justificativa das escolhas.
