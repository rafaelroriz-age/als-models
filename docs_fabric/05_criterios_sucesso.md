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
| Vendas (faturamento) | MAPE / MAE por mês, por segmento e por cliente |
| Convergência | Acompanhar o erro ao longo do mês (a planilha atual converge perto do dia 20) |

## Critérios complementares

- **Convergência temporal**: o forecast semanal deve convergir para o realizado à medida que o período avança.
- **Correlação consumo→venda**: quantificar corretamente a relação entre amostras processadas e faturamento (a "projeção por amostra" da planilha).
- **Sinais de ação**: detectar queda >20% nas amostras e "compartimento churn" (a avaliação de valor comercial, além da acurácia pura).
- **Calibração de incerteza** (se intervalo for entregue): a faixa reportada deve conter o realizado na proporção declarada.

## Critério de sucesso do entregável

- Modelo **consumível pelo ambiente** (modelo semântico ou API/endpoint), não um notebook.
- Roda na capacidade F8 sem degradar o agente (FinOps respeitado).
- Transparência de metodologia/ferramentas e justificativa das escolhas.
