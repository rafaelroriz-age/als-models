# ALS OIL & LUBRICANTS
## Escopo do Projeto — Previsão de TAT & Volume
### Engajamento freelance de ciência de dados

## 1. Objetivo

Este documento define o que gostaríamos que você construísse e o contexto necessário para dimensionar o esforço. Não estamos pedindo que você se comprometa com nada ainda — apenas que retorne com uma abordagem proposta, as ferramentas que usaria, uma estimativa do tempo envolvido e quaisquer dúvidas que tiver.

## 2. Contexto da empresa e do processo

A ALS Oil & Lubricants é um laboratório de análise de lubrificantes e monitoramento de condições. Os clientes nos enviam amostras de óleo para monitorar a saúde dos equipamentos, estender os intervalos de troca de óleo e reduzir paradas não programadas. Cada amostra passa por três estágios:

- **CRD** — a amostra é recebida e registrada. (Apenas registro; não conta no TAT.)
- **Laboratório** — a amostra passa pelos seus testes. Primeira e mais demorada parte do TAT.
- **Interpretação** — os resultados são revisados e interpretados. Segunda parte do TAT.

Algumas amostras são enviadas para re-teste, voltando ao Laboratório e à Interpretação. O relógio do TAT **não é zerado** — o tempo extra é somado, então re-testes aumentam diretamente o TAT daquela amostra.

Uma amostra passa por vários testes (chamamos de ensaios, também referidos como análises). Os ensaios são agrupados em grupos de trabalho (workgroups), e os grupos de trabalho em pacotes (também chamados de planos de análise). Esses agrupamentos, juntamente com o laboratório/local, são as unidades pelas quais gerenciamos nossa carga de trabalho — portanto, a previsão deve poder ser produzida para qualquer um deles.

## 3. Glossário

| Termo | Significado |
|-------|-------------|
| TAT | Turnaround Time — tempo total de processamento nas etapas de Laboratório e Interpretação. Corre continuamente; não pausa em fins de semana ou feriados. |
| Faixa de prazo (deadline band) | TAT máximo permitido para uma amostra (48 / 72 / 96 / 120 h). Fixo por amostra conforme tipo de óleo, equipamento, compartimento e atributos semelhantes — não é escolhido livremente. |
| Prazo cumprido | A amostra foi concluída dentro de sua faixa de prazo, medida a partir do timestamp de recebimento. |
| % On-time (dentro do prazo) | Participação de amostras que cumpriram o prazo. Nossa meta de serviço é de pelo menos 90% ao mês. |
| Ensaio | Um teste individual executado em uma amostra. Sinônimos: análise, teste. |
| Grupo de trabalho (workgroup) | Um grupo de ensaios. |
| Pacote | Um grupo de grupos de trabalho. Sinônimo: plano de análise. |
| S360 | Nosso LIMS (Sistema de Gerenciamento de Informações de Laboratório) — a fonte dos dados. |
| O agente | O sistema automatizado existente ao qual seu modelo se conecta; ele chama o modelo sob demanda para devolver previsões aos usuários. |

## 4. O que queremos que você construa

Estando no meio de um período, prever como aquele período terminará para uma entidade escolhida — tanto o resultado de TAT / on-time quanto o volume de amostras. A previsão se atualiza conforme o período avança.

O período é flexível — um dia, uma semana, um mês ou um intervalo personalizado — dependendo do que o usuário precisar, para ambos os resultados. (O mês é nossa referência principal porque a meta de 90% on-time é mensal.) A previsão também deve poder ser produzida por entidade: a operação inteira, ou um laboratório, pacote ou grupo de trabalho específico.

### Entrega e como será usada

- Um modelo que roda de forma autônoma (não um notebook ou relatório manual), integrado ao nosso agente existente.
- Atualizado sob demanda: quando um usuário pergunta ao agente, o modelo puxa os dados mais recentes e devolve uma previsão atualizada para a entidade e o período solicitados.
- Os principais usuários são gerentes de laboratório e equipe operacional, então o resultado deve ser simples de ler — um número claro mais uma noção de confiança — mesmo que o método por trás seja sofisticado.

Definiríamos a interface agente-modelo (entradas: entidade, data de referência, período-alvo; saída: previsão mais intervalo de incerteza) em conjunto com você.

## 5. Dados que você receberá

Você extrairá dados do nosso LIMS, o S360. Ele provavelmente já contém tudo o que você precisa; se algo estiver faltando, forneceremos com base nos seus requisitos. Não há dicionário de dados — você precisará descobrir as estruturas das tabelas por conta própria.

### Espere dados imperfeitos

Os dados refletem registros reais, então planeje-se para valores ausentes, outliers ocasionais e alguns erros de digitação. Perceber e lidar com isso faz parte do trabalho.

Observe também: no meio de um período, muitas amostras foram recebidas mas ainda não concluídas, então seu TAT final e seu status on-time são desconhecidos. A forma como você trata essas amostras em andamento (censuradas) importa para a previsão.

## 6. Ambiente e ferramentas

- Linguagem: Python.
- Roda na sua própria máquina; o modelo é posteriormente integrado ao nosso agente.
- Acesso aos dados: S360 (nosso LIMS).

## 7. Como julgaremos o sucesso

Pela precisão da previsão — quão próxima a previsão de meio de período está do resultado real. A forma natural de demonstrar isso é o backtesting: para períodos passados, posicione-se em um ponto intermediário usando apenas os dados disponíveis naquele momento, preveja o resultado e compare. Medidas úteis: erro médio no volume (MAE / MAPE); erro em pontos percentuais no % on-time, especialmente se sinaliza corretamente os meses em risco de não atingir 90%; e se o intervalo de confiança que você reporta está bem calibrado.

## 8. O que gostaríamos de receber de você

- Sua abordagem proposta e as ferramentas/bibliotecas que usaria.
- Uma estimativa do tempo que o trabalho levará, com as premissas por trás dela.
- Quaisquer dúvidas ou informações que você gostaria de ter antes de começar.

---

*Confidencial.*
