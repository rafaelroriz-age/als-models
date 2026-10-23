# Requisitos

## Requisitos de negócio (escopo da fase 1)

Dois KPIs, nesta ordem de dependência:

1. **Forecast de consumo de amostras** — prever quantas amostras cada cliente/equipamento vai gerar em um período.
   - Duas visões: **Real** (histórico/consumo do cliente) e **Potencial** (benchmark de clientes similares).
   - Granularidade: cliente → equipamento → compartimento; agregável por tipo de equipamento, setor e segmento.
   - Sinais de ação: queda >20% nas amostras do cliente; "compartimento churn".
2. **Forecast de vendas** — prever faturamento (predict revenue), derivado do consumo, idealmente semanal, mirando o EBIT.
   - Composição por componentes: recorrente, não recorrente ativa, novos, reativados, churn, variável de mercado.
   - Cross-check mensal (Zoho) para evitar dupla contagem.
   - Projeção por amostra processada (quantificar a correlação consumo→venda).

Ficam para fases seguintes: hub de notícias/mercado por setor, camada de segmentação de informação estratégica.

## Requisitos funcionais

- Modelo **consumível pelo ambiente** (modelo semântico no Fabric ou API/endpoint), **não** um notebook.
- A forma final de entrega faz parte da investigação (semântico vs endpoint).
- Pipeline própria com pré e pós-processamento; joins faturamento × amostras no pré-processamento (SQL).
- Medir as métricas que os times usam, validar adequação e propor alternativas com ganho — sempre validadas antes de entrar no modelo.
- Autonomia de metodologia/ferramentas, com transparência do que é usado e por quê.

## Requisitos não funcionais

| Requisito | Detalhe |
|-----------|---------|
| Ecossistema | Azure / Microsoft Fabric (lakehouse no OneLake). |
| Linguagem | Python (notebooks Spark) + SQL no pré-processamento. |
| Custo (FinOps) | Capacidade F8 compartilhada com o agente; preferir ML clássico; mensurar custo × acurácia; comparar modelos. |
| LLM | Permitido em pré/pós-processamento, de preferência modelos de menor custo. |
| Qualidade de dados | great expectations / pytest nos notebooks como parte da metodologia. |
| Escala | ~5 milhões de amostras/ano; histórico desde 2022; cálculos ao vivo são pesados. |

## Contrato de interface (a definir em conjunto)

| Campo | Tipo | Notas |
|-------|------|-------|
| entidade (cliente / equipamento / setor / segmento) | entrada | granularidade da previsão |
| data de referência | entrada | ponto "as-of" da previsão |
| período-alvo | entrada | semana / mês (semanal é desejável para vendas) |
| previsão | saída | amostras previstas e/ou faturamento previsto |
| intervalo de incerteza | saída | faixa de confiança |

## Premissas e pontos a validar (perguntas em aberto)

1. Origem do **Annual Sample Potential**: calculadora ou benchmark de similares? Quais parâmetros?
2. **Ticket médio e conversão** atuais (vs. R$ 1.950 / 5% de out/2022)?
3. **Regra do recorrente** confirmada (≥6 meses/12, <90 dias, sem a taxa de 70%)?
4. **Composição do forecast de vendas** continua a mesma?
5. **Chave de equipamento (S360)** para o join — qual campo exato?
6. **Sazonalidade por segmento**: há curva/dados além de "meses trabalhados/ano"?
7. Acesso ao lakehouse (S360, ERP, Zoho) liberado? Quais schemas/tabelas?
8. Existe histórico de forecasts salvos para medir acurácia retroativa?
