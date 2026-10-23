# Requisitos Funcionais

## Requisito central

Estando no meio de um período, prever como aquele período terminará para uma entidade escolhida:

1. **Resultado de TAT / on-time**
2. **Volume de amostras**

A previsão se atualiza conforme o período avança.

## Contrato de interface (a ser definido em conjunto)

| Campo | Tipo | Observações |
|-------|------|-------------|
| entidade | entrada | operação inteira / laboratório / pacote / grupo de trabalho |
| data de referência (as-of) | entrada | o ponto de vista de "meio do período" |
| período-alvo | entrada | dia / semana / mês / intervalo personalizado |
| previsão | saída | o(s) número(s) previsto(s) |
| intervalo de incerteza | saída | confiança / intervalo |

## Requisitos não funcionais / de entrega

- **Autônomo** — roda como um serviço, não um notebook ou relatório manual.
- **Integrado** — conecta-se ao agente existente.
- **Atualização sob demanda** — puxa os dados mais recentes do S360 quando solicitado.
- **Saída simples** — um número claro + confiança, legível por gerentes de laboratório e equipe operacional.
- **Linguagem** — Python.
- **Ambiente de execução** — roda na máquina do freelancer durante o desenvolvimento; posteriormente integrado ao agente.

## Premissas a validar (perguntas em aberto)

1. O que exatamente o "volume" conta — recebidas, concluídas ou ambas? (por entidade/período)
2. Quais timestamps existem no S360 (recebimento, início/fim do laboratório, fim da interpretação, eventos de re-teste)?
3. Como a faixa de prazo é armazenada/derivada por amostra?
4. A entidade (laboratório / pacote / grupo de trabalho) é diretamente relacionável às amostras no S360?
5. Há volume de dados históricos suficiente para backtesting (quantos meses/anos)?
