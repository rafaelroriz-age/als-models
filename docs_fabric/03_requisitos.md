# Requisitos

## Requisitos de negócio (escopo da fase 1)

Dois KPIs, nesta ordem de dependência:

1. **Forecast de consumo de amostras** — prever quantas amostras cada cliente/equipamento vai gerar em um período.
   - Duas visões: **Real** (histórico/consumo do cliente) e **Potencial** (benchmark de clientes similares).
   - Granularidade: cliente → equipamento → compartimento; agregável por tipo de equipamento, setor e segmento.
   - Sinais de ação: queda >20% nas amostras do cliente; "compartimento churn".
2. **Forecast de vendas** — prever faturamento (predict revenue), derivado do consumo, idealmente semanal. **Faturamento e EBIT são targets separados.**
   - Composição por componentes: recorrente, não recorrente ativa, churn, variável de mercado. **Novos e reativados: fora do escopo por ora.**
   - Cross-check mensal (Zoho) para evitar dupla contagem.
   - Projeção por amostra processada (quantificar a correlação consumo→venda).

Ficam para fases seguintes: hub de notícias/mercado por setor, camada de segmentação de informação estratégica.

> **Escopo definido (reunião de 21/10/2026):** o KPI 2 foca em clientes ativos recorrentes e não recorrentes ativos.

## Requisitos funcionais

- Modelo **consumível pelo ambiente**, **não** um notebook. O formato é definido após a prototipagem.
- Formato de entrega: **todas as hipóteses (dashboard HTML + SQL sobre as tabelas de saída, modelo semântico, API/MCP) serão prototipadas** para o cliente escolher.
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

## Hipóteses a testar e descobertas por dados

Decisões, hipóteses (H1–H4) e descobertas (R1–R7) estão em [13](13_revisao_alinhamento_reuniao_2026-10-21.md). Resumo:

- **Por protótipo:** oportunidades >80% somam ou só descontam; receita como venda de kit ou análise processada; formato de entrega.
- **Por dados:** origem do Annual Sample Potential, famílias da Calculadora, equipamentos ativos, taxa de retorno kit→amostra, chave de equipamento, regra E/OU da recorrência.
- **Ainda sem resposta:** meta de MAPE, cadência semanal obrigatória, hierarquia matriz/filial, janela de CU na F8.
