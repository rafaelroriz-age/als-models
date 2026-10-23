# Visão Geral do Projeto

## Resumo em uma frase

Construir um modelo de previsão autônomo que, estando no meio de um período, prevê como um período escolhido terminará para uma entidade escolhida — tanto o resultado de **TAT / on-time** quanto o **volume de amostras** — atualizado sob demanda por meio de um agente existente.

## Os dois alvos da previsão

| Saída | Definição | Referência principal |
|-------|-----------|----------------------|
| TAT / resultado on-time | Participação de amostras concluídas dentro da faixa de prazo | Meta de 90% on-time é mensal |
| Volume de amostras | Número de amostras processadas no período | Dia / semana / mês / intervalo personalizado |

## Flexibilidade de período

- Dia, semana, mês ou intervalo personalizado.
- O mês é a referência principal porque a meta de 90% é mensal.

## Flexibilidade de entidade

A previsão deve poder ser produzida para qualquer um dos seguintes:
- A operação inteira
- Um laboratório/local específico
- Um pacote específico (plano de análise)
- Um grupo de trabalho específico

## Principais entradas e saídas

**Entradas:** entidade, data de referência (as-of), período-alvo.
**Saída:** previsão mais intervalo de incerteza.

## O fluxo de trabalho (3 estágios por amostra)

1. **CRD** — recebida e registrada (não conta no TAT).
2. **Laboratório** — os testes são executados (primeira e mais demorada parte do TAT).
3. **Interpretação** — os resultados são revisados (segunda parte do TAT).

Re-testes voltam pelo Laboratório + Interpretação e **não zeram** o relógio do TAT — eles aumentam o TAT diretamente.

## Hierarquia dos agrupamentos

```
Amostra → Ensaios (testes/análises) → Grupos de trabalho → Pacotes (planos de análise) → Laboratório/Local → Operação
```

## Formato da entrega

- Modelo autônomo (não um notebook / relatório manual), integrado ao agente existente.
- Atualizado sob demanda quando um usuário pergunta ao agente.
- Saída simples e legível: um número claro + confiança, para gerentes de laboratório e equipe operacional.
