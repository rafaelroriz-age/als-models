# Critérios de Sucesso e Avaliação

## Juiz principal: precisão da previsão

Quão próxima a **previsão de meio de período** está do **resultado real**.

## Método de avaliação: backtesting

Para períodos passados, posicione-se em um ponto intermediário usando apenas os dados disponíveis naquele momento, preveja o resultado e compare com o que realmente aconteceu.

## Métricas

| Saída | Métrica |
|-------|---------|
| Volume | MAE / MAPE (erro médio) |
| % On-time | Erro em pontos percentuais, especialmente se sinaliza corretamente os meses em risco de não atingir 90% |
| Intervalo de confiança | Calibração — a incerteza reportada deve estar bem calibrada |

## O que "bem calibrado" significa na prática

Um intervalo de confiança de 90% deve conter o resultado real ~90% das vezes ao longo dos backtests. Esse é um diferencial importante e será verificado explicitamente.

## Ênfase na sinalização de risco

Sinalizar corretamente os meses em risco de ficar abaixo da meta de 90% on-time vale tanto quanto a precisão pontual. A avaliação deve rastrear a precisão/revocação das sinalizações de "risco", não apenas o erro bruto.

## Implicações para o design do backtesting

- Deve simular "apenas os dados disponíveis naquele momento" — sem vazamento de informação futura.
- Deve reproduzir a censura fielmente (remover informações de conclusão de amostras ainda não concluídas no ponto de referência).
- Deve rodar em muitos períodos e entidades para obter estimativas de erro estáveis.
